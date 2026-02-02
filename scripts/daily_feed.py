#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
#     "matplotlib",
#     "pillow",
# ]
# ///
"""Daily feed orchestrator - fetches, formats, and posts position updates.

This is the main entry point for the daily X feed. It orchestrates:
1. Fetching positions from Nansen API
2. Formatting into a Twitter thread (text or images)
3. Posting via Typefully API

Usage:
    uv run scripts/daily_feed.py [--dry-run] [--schedule=N] [--use-images]

Options:
    --dry-run       Preview without posting to Typefully
    --schedule=N    Schedule post N minutes from now
    --use-images    Generate table images instead of text

Environment Variables:
    NANSEN_API_KEY          Required. Nansen API key for position data
    TYPEFULLY_API_KEY       Required (unless --dry-run). Typefully API key
    TYPEFULLY_SOCIAL_SET_ID Optional. Social set ID (auto-discovered if not set)
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Optional imports for image generation
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

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


def truncate_label(label: str, max_len: int = 18) -> str:
    """Truncate label to fit in tweet."""
    if len(label) <= max_len:
        return label
    return label[:max_len - 1] + "…"


def format_position_row(rank: int, position: dict) -> str:
    """Format a single position as a table row."""
    side = position.get("side", "Unknown")
    side_emoji = "🟢" if side == "Long" else "🔴"

    label = position.get("address_label") or ""
    address = position.get("address", "")
    position_value = position.get("position_value_usd", 0)
    upnl = position.get("upnl_usd", 0)
    entry_price = position.get("entry_price", 0)
    mark_price = position.get("mark_price", 0)

    # Format display name
    if label:
        display_name = truncate_label(label, 18)
    else:
        display_name = f"[{address[:8]}]" if address else "[unknown]"

    size_str = format_number(position_value)
    entry_str = format_price(entry_price)
    mark_str = format_price(mark_price)
    pnl_str = format_number(upnl, include_sign=True)
    pnl_emoji = "✅" if upnl >= 0 else "❌"

    return f"""{rank}. {display_name}
   {side_emoji} {side} | Size: {size_str}
   Entry: {entry_str} → Mark: {mark_str}
   {pnl_emoji} uPnL: {pnl_str}"""


def format_token_tweet(token: str, positions: list, is_first: bool = False) -> dict:
    """Format a token's top 10 positions into a single tweet."""
    if not positions:
        return {"text": f"${token}: No positions found"}

    longs = sum(1 for p in positions if p.get("side") == "Long")
    shorts = sum(1 for p in positions if p.get("side") == "Short")

    # Build header
    if is_first:
        date = datetime.now().strftime("%B %d, %Y")
        header = f"""🔥 ${token} Top {len(positions)} Positions
📅 {date}

🟢 {longs} Longs | 🔴 {shorts} Shorts
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    else:
        header = f"""${token} Top {len(positions)} Positions

🟢 {longs} Longs | 🔴 {shorts} Shorts
━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    # Build position rows
    rows = []
    for i, pos in enumerate(positions):
        rows.append(format_position_row(i + 1, pos))

    return {"text": header + "\n\n" + "\n\n".join(rows)}


def format_thread(data: dict) -> list[dict]:
    """Format all position data into Typefully posts array."""
    posts = []

    # Token tweets (BTC first with date, then others)
    for idx, token in enumerate(TOKENS):
        token_data = data.get(token, {})
        positions = []
        if isinstance(token_data, dict):
            positions = token_data.get("data", [])
        elif isinstance(token_data, list):
            positions = token_data

        if positions:
            is_first = (idx == 0)
            posts.append(format_token_tweet(token, positions, is_first=is_first))

    # Footer tweet
    posts.append({"text": """📈 Data: @naborlabs
🤖 Powered by hyper-signals

Follow for daily updates!"""})

    return posts


# === Image Generation ===
IMAGE_COLORS = {
    "bg": "#0d1117",
    "header_bg": "#161b22",
    "row_even": "#0d1117",
    "row_odd": "#161b22",
    "text": "#e6edf3",
    "text_muted": "#8b949e",
    "green": "#3fb950",
    "red": "#f85149",
    "border": "#30363d",
    "accent": "#58a6ff",
}


def strip_emojis(text: str) -> str:
    """Remove emojis from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U0000200B-\U0000200D"
        "\U0000FE0F"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text).strip()


def img_truncate_label(label: str, max_len: int = 20) -> str:
    """Truncate label for image table."""
    label = strip_emojis(label)
    if len(label) <= max_len:
        return label
    return label[:max_len - 1] + "..."


def img_format_address(address: str) -> str:
    """Format address for image table."""
    if not address or len(address) < 10:
        return "unknown"
    return f"{address[:6]}...{address[-4:]}"


def generate_token_image(
    token: str,
    positions: list,
    output_path: Path,
    show_date: bool = True,
) -> Path:
    """Generate a styled table image for positions."""
    if not HAS_MATPLOTLIB:
        raise RuntimeError("matplotlib not installed")

    headers = ["#", "Label", "Wallet", "Side", "Size", "Leverage", "Entry", "Mark", "Liq Price", "uPnL"]

    rows = []
    for i, pos in enumerate(positions, 1):
        label = pos.get("address_label", "") or ""
        address = pos.get("address", "")
        side = pos.get("side", "")
        size = pos.get("position_value_usd", 0)
        leverage = pos.get("leverage", "")
        entry = pos.get("entry_price", 0)
        mark = pos.get("mark_price", 0)
        liq = pos.get("liquidation_price", 0)
        upnl = pos.get("upnl_usd", 0)

        rows.append([
            str(i),
            img_truncate_label(label, 18) if label else "-",
            img_format_address(address),
            side,
            format_number(size),
            leverage,
            format_price(entry),
            format_price(mark),
            format_price(liq),
            format_number(upnl, include_sign=True),
        ])

    longs = sum(1 for p in positions if p.get("side") == "Long")
    shorts = len(positions) - longs

    fig_width = 16
    fig_height = 1.5 + len(rows) * 0.5
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=IMAGE_COLORS["bg"])
    ax.set_facecolor(IMAGE_COLORS["bg"])
    ax.axis('off')

    date_str = datetime.now().strftime("%B %d, %Y")
    title = f"${token} Top {len(positions)} Positions"
    if show_date:
        title += f"  •  {date_str}"

    ax.text(0.5, 0.95, title, transform=ax.transAxes, fontsize=18, fontweight='bold',
            color=IMAGE_COLORS["text"], ha='center', va='top', fontfamily='monospace')

    ax.text(0.42, 0.88, f"{longs} Longs", transform=ax.transAxes, fontsize=12,
            color=IMAGE_COLORS["green"], ha='right', va='top', fontfamily='monospace', fontweight='bold')
    ax.text(0.5, 0.88, "  |  ", transform=ax.transAxes, fontsize=12,
            color=IMAGE_COLORS["text_muted"], ha='center', va='top', fontfamily='monospace')
    ax.text(0.58, 0.88, f"{shorts} Shorts", transform=ax.transAxes, fontsize=12,
            color=IMAGE_COLORS["red"], ha='left', va='top', fontfamily='monospace', fontweight='bold')

    col_widths = [0.03, 0.16, 0.12, 0.06, 0.09, 0.07, 0.10, 0.10, 0.12, 0.10]

    table = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc='center',
        loc='center',
        colWidths=col_widths,
        bbox=[0.02, 0.05, 0.96, 0.78]
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)

    for key, cell in table.get_celld().items():
        row, col = key
        cell.set_edgecolor(IMAGE_COLORS["border"])
        cell.set_linewidth(0.5)

        if row == 0:
            cell.set_facecolor(IMAGE_COLORS["header_bg"])
            cell.set_text_props(color=IMAGE_COLORS["accent"], fontweight='bold', fontfamily='monospace')
            cell.set_height(0.08)
        else:
            bg_color = IMAGE_COLORS["row_even"] if row % 2 == 0 else IMAGE_COLORS["row_odd"]
            cell.set_facecolor(bg_color)
            cell.set_text_props(fontfamily='monospace')

            text = cell.get_text().get_text()

            if col == 3:
                if text == "Long":
                    cell.set_text_props(color=IMAGE_COLORS["green"], fontweight='bold', fontfamily='monospace')
                elif text == "Short":
                    cell.set_text_props(color=IMAGE_COLORS["red"], fontweight='bold', fontfamily='monospace')
                else:
                    cell.set_text_props(color=IMAGE_COLORS["text"], fontfamily='monospace')
            elif col == 9:
                if text.startswith("+"):
                    cell.set_text_props(color=IMAGE_COLORS["green"], fontweight='bold', fontfamily='monospace')
                elif text.startswith("-"):
                    cell.set_text_props(color=IMAGE_COLORS["red"], fontweight='bold', fontfamily='monospace')
                else:
                    cell.set_text_props(color=IMAGE_COLORS["text"], fontfamily='monospace')
            else:
                cell.set_text_props(color=IMAGE_COLORS["text"], fontfamily='monospace')

    footer = "Data: Nansen  |  Powered by hyper-signals"
    ax.text(0.5, 0.01, footer, transform=ax.transAxes, fontsize=9,
            color=IMAGE_COLORS["text_muted"], ha='center', va='bottom', fontfamily='monospace')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor=IMAGE_COLORS["bg"],
                edgecolor='none', bbox_inches='tight', pad_inches=0.2)
    plt.close()

    return output_path


def generate_all_images(data: dict, output_dir: Path) -> list[Path]:
    """Generate table images for all tokens."""
    output_dir.mkdir(exist_ok=True)
    images = []

    for idx, token in enumerate(TOKENS):
        token_data = data.get(token, {})
        positions = []
        if isinstance(token_data, dict):
            positions = token_data.get("data", [])
        elif isinstance(token_data, list):
            positions = token_data

        if not positions:
            continue

        output_path = output_dir / f"{token.lower()}_positions.png"
        show_date = (idx == 0)

        generate_token_image(token, positions, output_path, show_date=show_date)
        images.append(output_path)
        log_info(f"Generated image: {output_path}")

    return images


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


def upload_media_to_typefully(api_key: str, social_set_id: int, file_path: Path) -> str:
    """Upload media to Typefully and return media_id.

    Typefully uses a 3-step upload flow:
    1. Request presigned URL from /v2/social-sets/{id}/media/upload
    2. Upload file to S3 presigned URL
    3. Use media_id in draft posts
    """
    with httpx.Client() as client:
        # Step 1: Request presigned upload URL
        response = client.post(
            f"{TYPEFULLY_API_URL}/social-sets/{social_set_id}/media/upload",
            headers=get_typefully_headers(api_key),
            json={"file_name": file_path.name},
            timeout=30.0,
        )
        response.raise_for_status()
        upload_data = response.json()

        upload_url = upload_data.get("upload_url")
        media_id = upload_data.get("media_id")

        if not upload_url or not media_id:
            raise RuntimeError(f"Invalid upload response: {upload_data}")

        # Step 2: Upload file to S3 presigned URL
        with open(file_path, "rb") as f:
            file_data = f.read()

        upload_response = client.put(
            upload_url,
            content=file_data,
            timeout=120.0,
        )
        upload_response.raise_for_status()

        # Step 3: Check media status (optional but recommended)
        for _ in range(10):  # Poll for up to 10 seconds
            status_response = client.get(
                f"{TYPEFULLY_API_URL}/social-sets/{social_set_id}/media/{media_id}",
                headers=get_typefully_headers(api_key),
                timeout=30.0,
            )
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("status") == "ready":
                    break
                elif status_data.get("status") == "failed":
                    raise RuntimeError(f"Media processing failed: {status_data}")
            time.sleep(1)

        log_info(f"Uploaded {file_path.name} -> media_id: {media_id}")
        return media_id


def format_thread_with_images(data: dict, media_ids: list[str]) -> list[dict]:
    """Format thread posts with image attachments."""
    posts = []

    for idx, token in enumerate(TOKENS):
        token_data = data.get(token, {})
        positions = []
        if isinstance(token_data, dict):
            positions = token_data.get("data", [])
        elif isinstance(token_data, list):
            positions = token_data

        if not positions:
            continue

        longs = sum(1 for p in positions if p.get("side") == "Long")
        shorts = len(positions) - longs

        # Simple text caption with the image
        if idx == 0:
            date_str = datetime.now().strftime("%B %d, %Y")
            text = f"🔥 ${token} Top {len(positions)} Positions\n📅 {date_str}\n\n🟢 {longs} Longs | 🔴 {shorts} Shorts"
        else:
            text = f"${token} Top {len(positions)} Positions\n\n🟢 {longs} Longs | 🔴 {shorts} Shorts"

        post = {"text": text}
        if idx < len(media_ids):
            post["media_ids"] = [media_ids[idx]]

        posts.append(post)

    # Footer tweet
    posts.append({"text": """📈 Data: @naborlabs
🤖 Powered by hyper-signals

Follow for daily updates!"""})

    return posts


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
def parse_args() -> tuple[bool, int | None, bool, bool]:
    """Parse command line arguments.

    Returns:
        Tuple of (dry_run, schedule_minutes, health_check_only, use_images)
    """
    dry_run = "--dry-run" in sys.argv
    health_check_only = "--health-check" in sys.argv
    use_images = "--use-images" in sys.argv
    schedule_minutes = None

    for arg in sys.argv[1:]:
        if arg.startswith("--schedule="):
            try:
                schedule_minutes = int(arg.split("=")[1])
            except (ValueError, IndexError):
                log_error(f"Invalid schedule value: {arg}")
                sys.exit(1)

    return dry_run, schedule_minutes, health_check_only, use_images


def main() -> int:
    """Main entry point."""
    dry_run, schedule_minutes, health_check_only, use_images = parse_args()

    # Load .env file
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    log_info("=" * 50)
    log_info("Hyperliquid Daily Feed")
    if use_images:
        log_info("Mode: Image tables")
    log_info("=" * 50)

    # Validate environment
    env = validate_environment(dry_run)

    # Health check mode
    if health_check_only:
        log_info("Running health check...")
        status = health_check(env)
        print(json.dumps(status, indent=2))
        return 0 if all([status["nansen"], status.get("typefully", True)]) else 1

    # Get social set ID early (needed for image uploads)
    social_set_id = env.get("typefully_social_set_id")
    if not social_set_id and not dry_run:
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

    # Fetch positions
    log_info("Fetching positions from Nansen API...")
    try:
        data = fetch_all_positions(TOKENS, env["nansen_api_key"])
    except Exception as e:
        log_error(f"Failed to fetch positions: {e}")
        return 1

    # Generate images if requested
    media_ids = []
    image_paths = []
    if use_images:
        log_info("Generating table images...")
        output_dir = Path(__file__).parent.parent / "output"
        try:
            image_paths = generate_all_images(data, output_dir)
            log_info(f"Generated {len(image_paths)} images")

            # Upload images (unless dry-run)
            if not dry_run:
                log_info("Uploading images to Typefully...")
                for img_path in image_paths:
                    try:
                        media_id = upload_media_to_typefully(
                            env["typefully_api_key"],
                            int(social_set_id),
                            img_path
                        )
                        media_ids.append(media_id)
                    except Exception as e:
                        log_warn(f"Failed to upload {img_path.name}: {e}")
        except Exception as e:
            log_error(f"Failed to generate images: {e}")
            log_info("Falling back to text-only mode")
            use_images = False

    # Format thread
    log_info("Formatting thread...")
    if use_images:
        # For dry-run, use placeholder media_ids; for real posts, use uploaded ones
        placeholder_ids = [f"img_{i}" for i in range(len(image_paths))] if dry_run else media_ids
        posts = format_thread_with_images(data, placeholder_ids)
    else:
        posts = format_thread(data)
    log_info(f"Created {len(posts)} tweets")

    # Dry run output
    if dry_run:
        log_info("DRY RUN MODE - Thread preview:")
        for i, post in enumerate(posts, 1):
            print(f"\n--- Tweet {i} ---")
            print(post["text"])
            if post.get("media_ids"):
                print(f"[Image attached]")
        if use_images:
            print(f"\nGenerated images in: {output_dir}")
            for img in image_paths:
                print(f"  - {img.name}")
        print("\n" + "=" * 50)
        log_info("Dry run complete. No posts created.")
        return 0

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
