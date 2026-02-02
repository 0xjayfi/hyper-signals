#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""Daily feed orchestrator - fetches, formats, and posts position updates.

This is the main entry point for the daily X feed. It orchestrates:
1. Fetching positions from Nansen API
2. Formatting into a Twitter thread
3. Posting via Typefully API

Usage:
    uv run scripts/daily_feed.py [--dry-run] [--schedule=N]

Options:
    --dry-run       Preview without posting to Typefully
    --schedule=N    Schedule post N minutes from now

Environment Variables:
    NANSEN_API_KEY          Required. Nansen API key for position data
    TYPEFULLY_API_KEY       Required (unless --dry-run). Typefully API key
    TYPEFULLY_SOCIAL_SET_ID Optional. Social set ID (auto-discovered if not set)
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

# === Configuration ===
NANSEN_API_URL = "https://api.nansen.ai/api/v1/tgm/perp-positions"
TYPEFULLY_API_URL = "https://api.typefully.com/v2"
TOKENS = ["BTC", "ETH", "SOL", "HYPE"]
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


# === Logging ===
def log(level: str, msg: str) -> None:
    """Log message with timestamp and level."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}", file=sys.stderr)


def log_info(msg: str) -> None:
    log("INFO", msg)


def log_warn(msg: str) -> None:
    log("WARN", msg)


def log_error(msg: str) -> None:
    log("ERROR", msg)


# === Environment Validation ===
def validate_environment(dry_run: bool) -> dict:
    """Validate required environment variables.

    Args:
        dry_run: If True, Typefully keys are optional

    Returns:
        Dict with validated environment values

    Raises:
        SystemExit: If required variables are missing
    """
    env = {}
    errors = []

    # Nansen API key is always required
    env["nansen_api_key"] = os.environ.get("NANSEN_API_KEY")
    if not env["nansen_api_key"]:
        errors.append("NANSEN_API_KEY is not set")

    # Typefully keys are required unless dry-run
    env["typefully_api_key"] = os.environ.get("TYPEFULLY_API_KEY")
    env["typefully_social_set_id"] = os.environ.get("TYPEFULLY_SOCIAL_SET_ID")

    if not dry_run and not env["typefully_api_key"]:
        errors.append("TYPEFULLY_API_KEY is not set (required unless --dry-run)")

    if errors:
        for error in errors:
            log_error(error)
        log_error("Set missing environment variables or use --dry-run mode")
        sys.exit(1)

    return env


# === Nansen API ===
def fetch_positions_with_retry(
    token: str,
    api_key: str,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF,
) -> dict:
    """Fetch top 10 positions for a token with exponential backoff retry."""
    last_error: Exception | None = None
    backoff = initial_backoff

    for attempt in range(max_retries):
        try:
            with httpx.Client() as client:
                response = client.post(
                    NANSEN_API_URL,
                    headers={"apiKey": api_key, "Content-Type": "application/json"},
                    json={
                        "token_symbol": token,
                        "pagination": {"page": 1, "per_page": 10},
                        "order_by": [{"field": "position_value_usd", "direction": "DESC"}],
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException as e:
            last_error = e
            log_warn(f"Timeout fetching {token} (attempt {attempt + 1}/{max_retries})")

        except httpx.HTTPStatusError as e:
            last_error = e
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                log_error(f"Client error fetching {token}: {e.response.status_code}")
                raise

            log_warn(f"HTTP {e.response.status_code} fetching {token} (attempt {attempt + 1}/{max_retries})")

        except httpx.RequestError as e:
            last_error = e
            log_warn(f"Request error fetching {token} (attempt {attempt + 1}/{max_retries}): {e}")

        if attempt < max_retries - 1:
            log_info(f"Retrying in {backoff:.1f}s...")
            time.sleep(backoff)
            backoff *= 2

    raise RuntimeError(f"Failed to fetch {token} after {max_retries} attempts") from last_error


def fetch_all_positions(tokens: list[str], api_key: str) -> dict:
    """Fetch positions for all specified tokens."""
    results = {}
    errors = []

    for token in tokens:
        try:
            log_info(f"Fetching {token}...")
            results[token] = fetch_positions_with_retry(token, api_key)
            position_count = len(results[token].get("data", []))
            log_info(f"{token}: fetched {position_count} positions")
        except Exception as e:
            log_error(f"Failed to fetch {token}: {e}")
            errors.append({"token": token, "error": str(e)})
            results[token] = {"data": [], "error": str(e)}

    if errors:
        log_warn(f"Completed with {len(errors)} error(s)")

    return results


# === Thread Formatting ===
def format_number(n: float, include_sign: bool = False) -> str:
    """Format large numbers with K/M/B suffixes."""
    sign = ""
    if include_sign and n > 0:
        sign = "+"

    abs_n = abs(n)
    prefix = "-" if n < 0 else sign

    if abs_n >= 1_000_000_000:
        return f"{prefix}${abs_n / 1_000_000_000:.1f}B"
    if abs_n >= 1_000_000:
        return f"{prefix}${abs_n / 1_000_000:.1f}M"
    if abs_n >= 1_000:
        return f"{prefix}${abs_n / 1_000:.1f}K"
    return f"{prefix}${abs_n:.0f}"


def format_price(price: float) -> str:
    """Format price with appropriate precision."""
    if price >= 1000:
        return f"${price:,.0f}"
    if price >= 1:
        return f"${price:,.2f}"
    return f"${price:.4f}"


def format_token_tweet(token: str, positions: list) -> dict:
    """Format a single token's positions into a tweet."""
    if not positions:
        return {"text": f"${token}: No positions found"}

    longs = [p for p in positions if p.get("side") == "Long"]
    shorts = [p for p in positions if p.get("side") == "Short"]
    top = positions[0]

    side_emoji = "🟢" if top.get("side") == "Long" else "🔴"
    upnl = top.get("upnl_usd", 0)
    pnl_emoji = "✅" if upnl >= 0 else "❌"

    position_value = top.get("position_value_usd", 0)
    entry_price = top.get("entry_price", 0)
    label = top.get("address_label") or top.get("address", "Unknown")

    tweet = f"""${token} Top Positions

🟢 Longs: {len(longs)} | 🔴 Shorts: {len(shorts)}

Top: {label}
{side_emoji} {top.get('side', 'Unknown')} {format_number(position_value)}
└ Entry: {format_price(entry_price)}
└ {pnl_emoji} uPnL: {format_number(upnl, include_sign=True)}"""

    return {"text": tweet}


def format_thread(data: dict) -> list[dict]:
    """Format all position data into Typefully posts array."""
    posts = []
    date = datetime.now().strftime("%B %d, %Y")

    # Header tweet
    posts.append({"text": f"""🔥 Hyperliquid Daily Positions

📅 {date}

Top 10 positions for:
$BTC $ETH $SOL $HYPE

Thread 👇"""})

    # Token tweets
    for token in TOKENS:
        token_data = data.get(token, {})
        positions = []
        if isinstance(token_data, dict):
            positions = token_data.get("data", [])
        elif isinstance(token_data, list):
            positions = token_data

        if positions:
            posts.append(format_token_tweet(token, positions))

    # Footer tweet
    posts.append({"text": """📈 Data: @naborlabs
🤖 Powered by hyper-signals

Follow for daily updates!"""})

    return posts


# === Typefully API ===
def get_typefully_headers(api_key: str) -> dict:
    """Get auth headers for Typefully API."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def get_social_sets(api_key: str) -> list:
    """Get all connected social sets."""
    with httpx.Client() as client:
        response = client.get(
            f"{TYPEFULLY_API_URL}/social-sets",
            headers=get_typefully_headers(api_key),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["results"]


def post_to_typefully(
    api_key: str,
    social_set_id: int,
    posts: list[dict],
    schedule_minutes: int | None = None,
    dry_run: bool = False,
) -> dict:
    """Post thread to Typefully."""
    payload = {
        "platforms": {
            "x": {"enabled": True, "posts": posts},
            "threads": {"enabled": True, "posts": posts},
        },
        "draft_title": f"Hyperliquid Daily Positions - {datetime.now().strftime('%Y-%m-%d')}",
        "share": True,
    }

    if schedule_minutes:
        publish_at = datetime.now(timezone.utc) + timedelta(minutes=schedule_minutes)
        payload["publish_at"] = publish_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    if dry_run:
        return {"id": "dry_run", "status": "draft", "posts_count": len(posts)}

    with httpx.Client() as client:
        response = client.post(
            f"{TYPEFULLY_API_URL}/social-sets/{social_set_id}/drafts",
            headers=get_typefully_headers(api_key),
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


# === Health Check ===
def health_check(env: dict) -> dict:
    """Perform health check on required services.

    Returns:
        Dict with service status
    """
    status = {
        "nansen": False,
        "typefully": False,
        "timestamp": datetime.now().isoformat(),
    }

    # Check Nansen API
    try:
        with httpx.Client() as client:
            response = client.post(
                NANSEN_API_URL,
                headers={"apiKey": env["nansen_api_key"], "Content-Type": "application/json"},
                json={
                    "token_symbol": "BTC",
                    "pagination": {"page": 1, "per_page": 1},
                },
                timeout=10.0,
            )
            status["nansen"] = response.status_code == 200
    except Exception as e:
        log_warn(f"Nansen health check failed: {e}")

    # Check Typefully API
    if env.get("typefully_api_key"):
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{TYPEFULLY_API_URL}/social-sets",
                    headers=get_typefully_headers(env["typefully_api_key"]),
                    timeout=10.0,
                )
                status["typefully"] = response.status_code == 200
        except Exception as e:
            log_warn(f"Typefully health check failed: {e}")

    return status


# === CLI ===
def parse_args() -> tuple[bool, int | None, bool]:
    """Parse command line arguments.

    Returns:
        Tuple of (dry_run, schedule_minutes, health_check_only)
    """
    dry_run = "--dry-run" in sys.argv
    health_check_only = "--health-check" in sys.argv
    schedule_minutes = None

    for arg in sys.argv[1:]:
        if arg.startswith("--schedule="):
            try:
                schedule_minutes = int(arg.split("=")[1])
            except (ValueError, IndexError):
                log_error(f"Invalid schedule value: {arg}")
                sys.exit(1)

    return dry_run, schedule_minutes, health_check_only


def main() -> int:
    """Main entry point."""
    dry_run, schedule_minutes, health_check_only = parse_args()

    # Load .env file
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    log_info("=" * 50)
    log_info("Hyperliquid Daily Feed")
    log_info("=" * 50)

    # Validate environment
    env = validate_environment(dry_run)

    # Health check mode
    if health_check_only:
        log_info("Running health check...")
        status = health_check(env)
        print(json.dumps(status, indent=2))
        return 0 if all([status["nansen"], status.get("typefully", True)]) else 1

    # Fetch positions
    log_info("Fetching positions from Nansen API...")
    try:
        data = fetch_all_positions(TOKENS, env["nansen_api_key"])
    except Exception as e:
        log_error(f"Failed to fetch positions: {e}")
        return 1

    # Format thread
    log_info("Formatting thread...")
    posts = format_thread(data)
    log_info(f"Created {len(posts)} tweets")

    # Dry run output
    if dry_run:
        log_info("DRY RUN MODE - Thread preview:")
        for i, post in enumerate(posts, 1):
            print(f"\n--- Tweet {i} ---")
            print(post["text"])
        print("\n" + "=" * 50)
        log_info("Dry run complete. No posts created.")
        return 0

    # Get social set ID
    social_set_id = env.get("typefully_social_set_id")
    if not social_set_id:
        log_info("Auto-discovering social set...")
        try:
            social_sets = get_social_sets(env["typefully_api_key"])
            if not social_sets:
                log_error("No social sets found. Connect an account at typefully.com")
                return 1
            social_set = social_sets[0]
            social_set_id = str(social_set["id"])
            log_info(f"Using social set: {social_set.get('username', 'unknown')} (ID: {social_set_id})")
        except Exception as e:
            log_error(f"Failed to discover social sets: {e}")
            return 1

    # Post to Typefully
    action = "Creating draft" if not schedule_minutes else f"Scheduling draft ({schedule_minutes} min from now)"
    log_info(f"{action}...")

    try:
        result = post_to_typefully(
            api_key=env["typefully_api_key"],
            social_set_id=int(social_set_id),
            posts=posts,
            schedule_minutes=schedule_minutes,
            dry_run=False,
        )
    except httpx.HTTPStatusError as e:
        log_error(f"Typefully API error: {e.response.status_code} - {e.response.text}")
        return 1
    except Exception as e:
        log_error(f"Failed to post to Typefully: {e}")
        return 1

    log_info(f"Success! Draft ID: {result.get('id')}")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
