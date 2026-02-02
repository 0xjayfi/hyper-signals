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
POSITIONS_PER_TWEET = 5  # Split 10 positions into 2 tweets per token


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


def truncate_label(label: str, max_len: int = 12) -> str:
    """Truncate label to fit in tweet.

    Args:
        label: Original label
        max_len: Maximum length

    Returns:
        Truncated label
    """
    if len(label) <= max_len:
        return label
    return label[:max_len-1] + "…"


def format_address(address: str) -> str:
    """Format address as shortened hex.

    Args:
        address: Full wallet address

    Returns:
        Shortened address like [0x1234]
    """
    if not address or len(address) < 10:
        return "[unknown]"
    return f"[{address[:6]}]"


def format_position_line(rank: int, position: dict) -> str:
    """Format a single position as a compact line.

    Args:
        rank: Position rank (1-10)
        position: Position dictionary

    Returns:
        Formatted line like "1. Label [0x1234] 🟢 $65M +$2M"
    """
    side_emoji = "🟢" if position.get("side") == "Long" else "🔴"

    label = position.get("address_label") or ""
    address = position.get("address", "")
    position_value = position.get("position_value_usd", 0)
    upnl = position.get("upnl_usd", 0)
    entry_price = position.get("entry_price", 0)

    # Format components
    label_str = truncate_label(label, 12) if label else ""
    addr_str = format_address(address)
    size_str = format_number(position_value)
    pnl_str = format_number(upnl, include_sign=True)
    entry_str = format_price(entry_price)

    # Build line: "1. Label [0x1234] 🟢 $65M @ $98K → +$2M"
    if label_str:
        return f"{rank}. {label_str} {addr_str}\n   {side_emoji} {size_str} @ {entry_str} → {pnl_str}"
    else:
        return f"{rank}. {addr_str}\n   {side_emoji} {size_str} @ {entry_str} → {pnl_str}"


def format_token_tweets(token: str, positions: list, is_first: bool = False) -> List[dict]:
    """Format a token's positions into multiple tweets.

    Args:
        token: Token symbol (BTC, ETH, etc.)
        positions: List of position dictionaries
        is_first: Whether this is the first token (adds date header)

    Returns:
        List of dicts with text keys containing formatted tweets
    """
    if not positions:
        return [{"text": f"${token}: No positions found"}]

    tweets = []
    total_positions = len(positions)

    # Count longs and shorts
    longs = sum(1 for p in positions if p.get("side") == "Long")
    shorts = sum(1 for p in positions if p.get("side") == "Short")

    # Split positions into chunks
    for chunk_idx in range(0, total_positions, POSITIONS_PER_TWEET):
        chunk = positions[chunk_idx:chunk_idx + POSITIONS_PER_TWEET]
        chunk_num = (chunk_idx // POSITIONS_PER_TWEET) + 1
        total_chunks = (total_positions + POSITIONS_PER_TWEET - 1) // POSITIONS_PER_TWEET

        # Build header
        if chunk_idx == 0:
            # First tweet for this token - include summary
            if is_first:
                date = datetime.now().strftime("%B %d, %Y")
                header = f"🔥 ${token} Top {total_positions} Positions\n📅 {date}\n\n🟢 {longs} Longs | 🔴 {shorts} Shorts"
            else:
                header = f"${token} Top {total_positions} Positions\n\n🟢 {longs} Longs | 🔴 {shorts} Shorts"
        else:
            # Continuation tweet
            header = f"${token} Positions ({chunk_num}/{total_chunks})"

        # Format position lines
        lines = [header, ""]
        for i, pos in enumerate(chunk):
            rank = chunk_idx + i + 1
            lines.append(format_position_line(rank, pos))

        tweets.append({"text": "\n".join(lines)})

    return tweets


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

    # Add token tweets (BTC first, then others)
    for idx, token in enumerate(TOKENS):
        token_data = data.get(token, {})

        # Handle different data structures
        positions = []
        if isinstance(token_data, dict):
            positions = token_data.get("data", [])
        elif isinstance(token_data, list):
            positions = token_data

        if positions:
            is_first = (idx == 0)
            posts.extend(format_token_tweets(token, positions, is_first=is_first))

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
