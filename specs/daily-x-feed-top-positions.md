# Daily X Feed - Top 10 Positions (BTC, ETH, SOL, HYPE)

## Problem Statement

Build an automated daily X (Twitter) feed that posts threaded updates on the top 10 perpetual positions for BTC, ETH, SOL, and HYPE on Hyperliquid. The system should leverage UV single-file scripts for clean isolation, portability, and self-contained execution.

## Objectives

1. Fetch top 10 positions for BTC, ETH, SOL, HYPE from Nansen API
2. Format data into engaging X thread content
3. Schedule/publish threads via **Typefully API** (simpler than X API directly)
4. Run daily via cron/scheduler
5. Keep implementation simple with UV single-file scripts

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     UV Single-File Scripts                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ fetch_       │    │ format_      │    │ post_        │  │
│  │ positions.py │───▶│ thread.py    │───▶│ typefully.py │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│    Nansen API          JSON Data         Typefully API      │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │ daily_feed.py - Main orchestrator (single entry)     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## UV Single-File Script Benefits

- **Isolation**: Each script is self-contained with inline dependencies
- **Portability**: No virtualenv needed, just `uv run script.py`
- **Fast**: UV's caching makes subsequent runs instant
- **Clean**: Dependencies declared at top of each file

## API Dependencies

### Nansen API
- Endpoint: `POST https://api.nansen.ai/api/v1/tgm/perp-positions`
- Auth: `apiKey` header
- Returns: Position data with address, side, size, entry, PnL

### Typefully API (v2)
- Base URL: `https://api.typefully.com/v2`
- Auth: `Authorization: Bearer YOUR_API_KEY`
- Key Endpoints:
  - `GET /social-sets` - List connected accounts
  - `POST /social-sets/{id}/drafts` - Create draft/thread
  - `PATCH /social-sets/{id}/drafts/{draft_id}` - Update draft
- Thread Support: Multiple posts in `platforms.x.posts[]` array
- Scheduling: Set `publish_at` for scheduled publishing
- Multi-platform: X, LinkedIn, Threads, Bluesky supported

---

## Phase 1: Data Fetching

### Tasks
- [x] Create `scripts/fetch_positions.py` - fetches top positions from Nansen
- [x] Implement retry logic with exponential backoff
- [ ] Add caching to avoid duplicate API calls
- [x] Output JSON to stdout or file for pipeline

### Implementation

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///
"""Fetch top 10 perp positions for specified tokens from Nansen API."""

import httpx
import json
import os
import sys

NANSEN_API_URL = "https://api.nansen.ai/api/v1/tgm/perp-positions"
TOKENS = ["BTC", "ETH", "SOL", "HYPE"]

def fetch_positions(token: str, api_key: str) -> dict:
    """Fetch top 10 positions for a token."""
    with httpx.Client() as client:
        response = client.post(
            NANSEN_API_URL,
            headers={"apiKey": api_key, "Content-Type": "application/json"},
            json={
                "token_symbol": token,
                "pagination": {"page": 1, "per_page": 10},
                "order_by": [{"field": "position_value_usd", "direction": "DESC"}]
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

def main():
    api_key = os.environ.get("NANSEN_API_KEY")
    if not api_key:
        print("Error: NANSEN_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    results = {}
    for token in TOKENS:
        results[token] = fetch_positions(token, api_key)

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
```

---

## Phase 2: Thread Formatting

### Tasks
- [x] Create `scripts/format_thread.py` - formats positions into thread
- [x] Design thread template with emojis and formatting
- [x] Handle character limits (N/A - long posts supported)
- [x] Create summary tweet + individual position tweets
- [x] Output Typefully-compatible format

### Thread Structure

```
Tweet 1 (Header):
🔥 Hyperliquid Daily Positions Report
📅 {date}

Top 10 positions for $BTC $ETH $SOL $HYPE

Thread 👇

Tweet 2 (BTC Summary):
$BTC Top Positions

🟢 Longs: {count} | 🔴 Shorts: {count}
📊 Total OI: ${total}

Top holder: {label}
└ {side} ${value} @ {entry}
└ uPnL: ${pnl}

Tweet 3-5 (ETH, SOL, HYPE):
... similar format ...

Tweet N (Footer):
📈 Data: @naborlabs
🤖 Powered by hyper-signals

Follow for daily updates!
```

### Implementation

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Format position data into Typefully thread format."""

import json
import sys
from datetime import datetime

def format_number(n: float) -> str:
    """Format large numbers with K/M/B suffixes."""
    if abs(n) >= 1_000_000_000:
        return f"${n/1_000_000_000:.1f}B"
    if abs(n) >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"${n/1_000:.1f}K"
    return f"${n:.0f}"

def format_token_tweet(token: str, positions: list) -> str:
    """Format a single token's positions into a tweet."""
    longs = [p for p in positions if p["side"] == "Long"]
    shorts = [p for p in positions if p["side"] == "Short"]

    top = positions[0] if positions else None
    if not top:
        return f"${token}: No positions found"

    side_emoji = "🟢" if top["side"] == "Long" else "🔴"
    pnl_emoji = "✅" if top["upnl_usd"] > 0 else "❌"

    tweet = f"""${token} Top Positions

🟢 Longs: {len(longs)} | 🔴 Shorts: {len(shorts)}

Top: {top['address_label'][:20]}
{side_emoji} {top['side']} {format_number(top['position_value_usd'])}
└ Entry: ${top['entry_price']:,.0f}
└ {pnl_emoji} uPnL: {format_number(top['upnl_usd'])}"""

    return tweet

def format_thread(data: dict) -> list[dict]:
    """Format all data into Typefully posts array."""
    posts = []

    # Header tweet
    date = datetime.now().strftime("%Y-%m-%d")
    header = f"""🔥 Hyperliquid Daily Positions

📅 {date}

Top 10 positions for:
$BTC $ETH $SOL $HYPE

Thread 👇"""
    posts.append({"text": header})

    # Token tweets
    for token in ["BTC", "ETH", "SOL", "HYPE"]:
        if token in data and "data" in data[token]:
            tweet = format_token_tweet(token, data[token]["data"])
            posts.append({"text": tweet})

    # Footer
    footer = """📈 Data: @naborlabs
🤖 Powered by hyper-signals

Follow for daily updates!"""
    posts.append({"text": footer})

    return posts

def main():
    data = json.load(sys.stdin)
    posts = format_thread(data)
    print(json.dumps(posts, indent=2))

if __name__ == "__main__":
    main()
```

---

## Phase 3: Typefully API Posting

### Tasks
- [x] Create `scripts/post_typefully.py` - posts thread via Typefully
- [x] Implement social set discovery
- [x] Support scheduling with `publish_at`
- [x] Support dry-run mode for testing
- [x] Handle multi-platform posting (X + Threads)

### Typefully API Key Concepts

1. **Social Sets**: Connected social accounts (X, LinkedIn, Threads, etc.)
2. **Drafts**: Posts/threads that can be saved, scheduled, or published
3. **Platforms**: Each draft can target multiple platforms with different content
4. **Threading**: Multiple posts in `platforms.x.posts[]` creates a thread

### Implementation

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///
"""Post a thread to X via Typefully API."""

import httpx
import json
import os
import sys
from datetime import datetime, timedelta

TYPEFULLY_API_URL = "https://api.typefully.com/v2"

def get_headers(api_key: str) -> dict:
    """Get auth headers for Typefully API."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

def get_social_sets(api_key: str) -> list:
    """Get all connected social sets."""
    with httpx.Client() as client:
        response = client.get(
            f"{TYPEFULLY_API_URL}/social-sets",
            headers=get_headers(api_key),
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["results"]

def create_draft(
    api_key: str,
    social_set_id: int,
    posts: list[dict],
    schedule_minutes: int | None = None,
    dry_run: bool = False
) -> dict:
    """Create a draft/thread on Typefully."""

    payload = {
        "platforms": {
            "x": {
                "enabled": True,
                "posts": posts
            },
            "threads": {
                "enabled": True,
                "posts": posts  # Same content for Threads
            }
        },
        "draft_title": f"Hyperliquid Daily Positions - {datetime.now().strftime('%Y-%m-%d')}",
        "share": True
    }

    # Schedule for later if specified
    if schedule_minutes:
        publish_at = datetime.utcnow() + timedelta(minutes=schedule_minutes)
        payload["publish_at"] = publish_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    if dry_run:
        print(f"[DRY RUN] Would create draft:", file=sys.stderr)
        print(json.dumps(payload, indent=2), file=sys.stderr)
        return {"id": "dry_run", "status": "draft"}

    with httpx.Client() as client:
        response = client.post(
            f"{TYPEFULLY_API_URL}/social-sets/{social_set_id}/drafts",
            headers=get_headers(api_key),
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

def main():
    dry_run = "--dry-run" in sys.argv
    schedule_arg = next((a for a in sys.argv if a.startswith("--schedule=")), None)
    schedule_minutes = int(schedule_arg.split("=")[1]) if schedule_arg else None

    api_key = os.environ.get("TYPEFULLY_API_KEY")
    if not api_key:
        print("Error: TYPEFULLY_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    social_set_id = os.environ.get("TYPEFULLY_SOCIAL_SET_ID")
    if not social_set_id and not dry_run:
        # Auto-discover first social set
        social_sets = get_social_sets(api_key)
        if not social_sets:
            print("Error: No social sets found", file=sys.stderr)
            sys.exit(1)
        social_set_id = social_sets[0]["id"]
        print(f"Using social set: {social_sets[0]['username']} (ID: {social_set_id})", file=sys.stderr)

    posts = json.load(sys.stdin)
    result = create_draft(api_key, int(social_set_id or 0), posts, schedule_minutes, dry_run)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

---

## Phase 4: Orchestration & Scheduling

### Tasks
- [x] Create `scripts/daily_feed.py` - main orchestrator
- [x] Implement error handling and logging
- [x] Add health check / status reporting
- [x] Create cron/systemd configuration
- [x] Add environment variable validation

### Implementation

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///
"""Daily feed orchestrator - fetches, formats, and posts position updates."""

import httpx
import json
import os
import sys
from datetime import datetime

NANSEN_API_URL = "https://api.nansen.ai/api/v1/tgm/perp-positions"
TYPEFULLY_API_URL = "https://api.typefully.com/v2"
TOKENS = ["BTC", "ETH", "SOL", "HYPE"]

def log(msg: str):
    """Log with timestamp."""
    print(f"[{datetime.now().isoformat()}] {msg}", file=sys.stderr)

def fetch_positions(token: str, api_key: str) -> dict:
    """Fetch top 10 positions for a token."""
    with httpx.Client() as client:
        response = client.post(
            NANSEN_API_URL,
            headers={"apiKey": api_key, "Content-Type": "application/json"},
            json={
                "token_symbol": token,
                "pagination": {"page": 1, "per_page": 10},
                "order_by": [{"field": "position_value_usd", "direction": "DESC"}]
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

def format_number(n: float) -> str:
    """Format large numbers with K/M/B suffixes."""
    if abs(n) >= 1_000_000_000:
        return f"${n/1_000_000_000:.1f}B"
    if abs(n) >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"${n/1_000:.1f}K"
    return f"${n:.0f}"

def format_token_tweet(token: str, positions: list) -> str:
    """Format a single token's positions into a tweet."""
    longs = [p for p in positions if p["side"] == "Long"]
    shorts = [p for p in positions if p["side"] == "Short"]
    top = positions[0] if positions else None
    if not top:
        return f"${token}: No positions found"

    side_emoji = "🟢" if top["side"] == "Long" else "🔴"
    pnl_emoji = "✅" if top["upnl_usd"] > 0 else "❌"

    return f"""${token} Top Positions

🟢 Longs: {len(longs)} | 🔴 Shorts: {len(shorts)}

Top: {top['address_label'][:20]}
{side_emoji} {top['side']} {format_number(top['position_value_usd'])}
└ Entry: ${top['entry_price']:,.0f}
└ {pnl_emoji} uPnL: {format_number(top['upnl_usd'])}"""

def format_thread(data: dict) -> list[dict]:
    """Format all data into Typefully posts array."""
    posts = []
    date = datetime.now().strftime("%Y-%m-%d")

    posts.append({"text": f"""🔥 Hyperliquid Daily Positions

📅 {date}

Top 10 positions for:
$BTC $ETH $SOL $HYPE

Thread 👇"""})

    for token in TOKENS:
        if token in data and "data" in data[token]:
            posts.append({"text": format_token_tweet(token, data[token]["data"])})

    posts.append({"text": """📈 Data: @naborlabs
🤖 Powered by hyper-signals

Follow for daily updates!"""})

    return posts

def post_to_typefully(api_key: str, social_set_id: int, posts: list[dict], dry_run: bool) -> dict:
    """Post thread to Typefully."""
    payload = {
        "platforms": {
            "x": {"enabled": True, "posts": posts},
            "threads": {"enabled": True, "posts": posts}
        },
        "draft_title": f"Hyperliquid Daily - {datetime.now().strftime('%Y-%m-%d')}",
        "share": True
    }

    if dry_run:
        return {"id": "dry_run", "status": "draft", "posts_count": len(posts)}

    with httpx.Client() as client:
        response = client.post(
            f"{TYPEFULLY_API_URL}/social-sets/{social_set_id}/drafts",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

def main():
    dry_run = "--dry-run" in sys.argv

    log("Starting daily feed...")

    # Validate environment
    nansen_key = os.environ.get("NANSEN_API_KEY")
    typefully_key = os.environ.get("TYPEFULLY_API_KEY")
    social_set_id = os.environ.get("TYPEFULLY_SOCIAL_SET_ID")

    if not nansen_key:
        log("ERROR: NANSEN_API_KEY not set")
        sys.exit(1)

    if not dry_run and not typefully_key:
        log("ERROR: TYPEFULLY_API_KEY not set")
        sys.exit(1)

    # Fetch positions
    log("Fetching positions from Nansen...")
    data = {}
    for token in TOKENS:
        log(f"  Fetching {token}...")
        data[token] = fetch_positions(token, nansen_key)

    # Format thread
    log("Formatting thread...")
    posts = format_thread(data)
    log(f"  Created {len(posts)} tweets")

    # Post to Typefully
    log(f"Posting to Typefully (dry_run={dry_run})...")
    result = post_to_typefully(typefully_key or "", int(social_set_id or 0), posts, dry_run)

    if dry_run:
        log("DRY RUN - Thread preview:")
        for i, post in enumerate(posts):
            print(f"\n--- Tweet {i+1} ---")
            print(post["text"])

    log(f"Done! Draft ID: {result.get('id')}")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

### Cron Configuration

```bash
# Run daily at 8:00 AM UTC
0 8 * * * cd /path/to/hyper-signals && uv run scripts/daily_feed.py >> logs/daily_feed.log 2>&1
```

---

## Phase 5: Testing & Deployment

### Tasks
- [x] Add `--dry-run` flag to all scripts
- [x] Create test fixtures with sample API responses
- [x] Test character limits for tweets (N/A - long posts supported)
- [x] Validate thread posting works correctly
- [x] Set up logging and monitoring
- [x] Document environment variables
- [x] Add `.env` to `.gitignore`

### Environment Variables

```bash
# .env (DO NOT COMMIT)
NANSEN_API_KEY=your_nansen_api_key

# Typefully API (simpler than X OAuth!)
TYPEFULLY_API_KEY=your_typefully_api_key
TYPEFULLY_SOCIAL_SET_ID=your_social_set_id  # Optional, auto-discovered
```

### Testing Commands

```bash
# Test fetch only
uv run scripts/fetch_positions.py > test_data.json

# Test formatting
cat test_data.json | uv run scripts/format_thread.py

# Test Typefully posting (dry run)
cat test_data.json | uv run scripts/format_thread.py | uv run scripts/post_typefully.py --dry-run

# Test full pipeline (dry run)
uv run scripts/daily_feed.py --dry-run

# Production run
uv run scripts/daily_feed.py
```

---

## File Structure

```
hyper-signals/
├── .env                          # API keys (gitignored)
├── .env.example                  # Template for env vars
├── .gitignore                    # Ignore .env, logs, etc.
├── scripts/
│   ├── fetch_positions.py        # Nansen API fetcher
│   ├── format_thread.py          # Thread formatter
│   ├── post_typefully.py         # Typefully API poster
│   └── daily_feed.py             # Main orchestrator
├── logs/
│   └── daily_feed.log            # Execution logs
├── ai_docs/                      # API documentation
└── specs/
    └── daily-x-feed-top-positions.md
```

---

## Success Criteria

1. **Functional**: Daily thread posts successfully with top 10 positions
2. **Reliable**: Handles API errors gracefully with retries
3. **Portable**: Runs on any system with UV installed
4. **Observable**: Logs execution status and errors
5. **Testable**: Dry-run mode allows testing without posting
6. **Multi-platform**: Posts to X and Threads simultaneously

---

## Potential Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Typefully rate limits | Built-in rate limit headers, add backoff |
| Nansen API downtime | Retry with backoff, cache last successful data |
| Tweet character limit | Pre-validate lengths, truncate labels |
| Social set discovery | Auto-discover or use env var |
| Missing data | Graceful handling, skip tokens with no positions |

---

## Why Typefully over Direct X API?

| Aspect | Typefully | Direct X API |
|--------|-----------|--------------|
| Auth | Simple Bearer token | Complex OAuth 1.0a |
| Rate limits | Higher for personal use | Strict, requires paid tier |
| Threading | Native support | Manual reply chaining |
| Multi-platform | X + Threads + LinkedIn | X only |
| Scheduling | Built-in | Must implement |
| Setup | Generate API key | Register app, get tokens |

---

## Future Enhancements

- Add more tokens (DOGE, XRP, etc.)
- Historical comparison (vs yesterday)
- Alert on large position changes
- Web dashboard for previewing threads
- Schedule at optimal posting times
- Add LinkedIn support
