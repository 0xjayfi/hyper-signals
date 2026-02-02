#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Format position data into Typefully thread format.

Reads position JSON from stdin and outputs a JSON array of {text: ...} objects
suitable for the Typefully API.

Usage:
    cat positions.json | uv run scripts/format_thread.py
    uv run scripts/fetch_positions.py | uv run scripts/format_thread.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import List, Dict

# Constants
TOKENS = ["BTC", "ETH", "SOL", "HYPE"]


def format_number(n: float, include_sign: bool = False) -> str:
    """Format large numbers with K/M/B suffixes.

    Args:
        n: Number to format
        include_sign: If True, prefix positive numbers with +

    Returns:
        Formatted string like "$1.5M" or "+$250K"
    """
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
    """Format price with appropriate precision.

    Args:
        price: Price value

    Returns:
        Formatted price string
    """
    if price >= 1000:
        return f"${price:,.0f}"
    if price >= 1:
        return f"${price:,.2f}"
    return f"${price:.4f}"


def format_header_tweet() -> dict:
    """Create the header tweet for the thread.

    Returns:
        Dict with text key containing the header tweet
    """
    date = datetime.now().strftime("%B %d, %Y")

    header = f"""🔥 Hyperliquid Daily Positions

📅 {date}

Top 10 positions for:
$BTC $ETH $SOL $HYPE

Thread 👇"""

    return {"text": header}


def format_token_tweet(token: str, positions: list) -> dict:
    """Format a single token's positions into a tweet.

    Args:
        token: Token symbol (BTC, ETH, etc.)
        positions: List of position dictionaries

    Returns:
        Dict with text key containing the formatted tweet
    """
    if not positions:
        return {"text": f"${token}: No positions found"}

    # Count longs and shorts
    longs = [p for p in positions if p.get("side") == "Long"]
    shorts = [p for p in positions if p.get("side") == "Short"]

    # Get top position
    top = positions[0]

    # Determine emojis based on position details
    side_emoji = "🟢" if top.get("side") == "Long" else "🔴"

    upnl = top.get("upnl_usd", 0)
    pnl_emoji = "✅" if upnl >= 0 else "❌"

    # Format position value and PnL
    position_value = top.get("position_value_usd", 0)
    entry_price = top.get("entry_price", 0)

    # Get label with fallback
    label = top.get("address_label") or top.get("address", "Unknown")

    # Build the tweet
    tweet = f"""${token} Top Positions

🟢 Longs: {len(longs)} | 🔴 Shorts: {len(shorts)}

Top: {label}
{side_emoji} {top.get('side', 'Unknown')} {format_number(position_value)}
└ Entry: {format_price(entry_price)}
└ {pnl_emoji} uPnL: {format_number(upnl, include_sign=True)}"""

    return {"text": tweet}


def format_footer_tweet() -> dict:
    """Create the footer tweet for the thread.

    Returns:
        Dict with text key containing the footer tweet
    """
    footer = """📈 Data: @naborlabs
🤖 Powered by hyper-signals

Follow for daily updates!"""

    return {"text": footer}


def format_thread(data: dict) -> List[Dict]:
    """Format all position data into Typefully posts array.

    Args:
        data: Dictionary with token keys and position data

    Returns:
        List of dicts with text keys, ready for Typefully API
    """
    posts = []

    # Add header
    posts.append(format_header_tweet())

    # Add token tweets
    for token in TOKENS:
        token_data = data.get(token, {})

        # Handle different data structures
        positions = []
        if isinstance(token_data, dict):
            positions = token_data.get("data", [])
        elif isinstance(token_data, list):
            positions = token_data

        if positions:
            posts.append(format_token_tweet(token, positions))

    # Add footer
    posts.append(format_footer_tweet())

    return posts


def main():
    """Main entry point."""
    # Read JSON from stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)

    # Format the thread
    posts = format_thread(data)

    # Output Typefully-compatible JSON
    print(json.dumps(posts, indent=2))


if __name__ == "__main__":
    main()
