# Hyper-Signals

Automated daily X (Twitter) feed that posts threaded updates on the top 10 perpetual positions for BTC, ETH, SOL, and HYPE on Hyperliquid.

## Features

- Fetches top 10 positions from Nansen API
- Formats data into engaging X thread content
- Posts via Typefully API (supports X + Threads)
- UV single-file scripts for portability
- Dry-run mode for testing
- Scheduling support

## Requirements

- [UV](https://github.com/astral-sh/uv) - Fast Python package manager
- Nansen API key
- Typefully API key

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys

# 2. Test the pipeline (dry run)
uv run scripts/daily_feed.py --dry-run

# 3. Post for real
uv run scripts/daily_feed.py
```

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/daily_feed.py` | Main orchestrator - fetches, formats, and posts |
| `scripts/fetch_positions.py` | Fetches positions from Nansen API |
| `scripts/format_thread.py` | Formats positions into thread JSON |
| `scripts/post_typefully.py` | Posts thread via Typefully API |

### Usage Examples

```bash
# Full pipeline (dry run)
uv run scripts/daily_feed.py --dry-run

# Full pipeline (post immediately)
uv run scripts/daily_feed.py

# Schedule post 30 minutes from now
uv run scripts/daily_feed.py --schedule=30

# Health check
uv run scripts/daily_feed.py --health-check

# Individual scripts (pipe together)
uv run scripts/fetch_positions.py > positions.json
cat positions.json | uv run scripts/format_thread.py > posts.json
cat posts.json | uv run scripts/post_typefully.py --dry-run

# Fetch specific tokens only
uv run scripts/fetch_positions.py --tokens=BTC,ETH
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NANSEN_API_KEY` | Yes | Nansen API key for position data |
| `TYPEFULLY_API_KEY` | Yes* | Typefully API key (*not required for --dry-run) |
| `TYPEFULLY_SOCIAL_SET_ID` | No | Social set ID (auto-discovered if not set) |

## Thread Format

```
Tweet 1: Header with date and tokens
Tweet 2: $BTC top positions summary
Tweet 3: $ETH top positions summary
Tweet 4: $SOL top positions summary
Tweet 5: $HYPE top positions summary
Tweet 6: Footer with attribution
```

Example tweet:

```
$BTC Top Positions

🟢 Longs: 7 | 🔴 Shorts: 3

Top: Whale_BTC_Long
🟢 Long $15.5M
└ Entry: $98,500
└ ✅ uPnL: +$850.0K
```

## Scheduling with Cron

```bash
# Run daily at 8:00 AM UTC
0 8 * * * cd /path/to/hyper-signals && uv run scripts/daily_feed.py >> logs/daily_feed.log 2>&1
```

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   daily_feed.py                          │
│                  (orchestrator)                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │ Nansen API     │  │ Format Thread  │  │ Typefully  │ │
│  │ (fetch)        │─▶│ (transform)    │─▶│ (post)     │ │
│  └────────────────┘  └────────────────┘  └────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Project Structure

```
hyper-signals/
├── .env                  # API keys (gitignored)
├── .env.example          # Template for env vars
├── scripts/
│   ├── daily_feed.py     # Main orchestrator
│   ├── fetch_positions.py
│   ├── format_thread.py
│   └── post_typefully.py
├── tests/
│   ├── fixtures/         # Sample API responses
│   └── test_pipeline.py
├── logs/                 # Execution logs
└── specs/                # Project specifications
```

## Testing

```bash
# Run pipeline tests
uv run tests/test_pipeline.py
```

## Why UV Single-File Scripts?

Each script is self-contained with inline dependencies:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
```

Benefits:
- **No virtualenv setup** - Just `uv run script.py`
- **Portable** - Copy one file, it works
- **Fast** - UV caches dependencies across scripts
- **Isolated** - Each script declares its own deps

## License

MIT
