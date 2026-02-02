#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "matplotlib",
#     "pillow",
# ]
# ///
"""Generate styled table images for position data.

Creates professional-looking table images suitable for social media posts.

Usage:
    echo '{"BTC": {"data": [...]}}' | uv run scripts/generate_table_image.py
    uv run scripts/fetch_positions.py --tokens=BTC | uv run scripts/generate_table_image.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.table import Table
import numpy as np


# === Styling ===
COLORS = {
    "bg": "#0d1117",           # Dark background
    "header_bg": "#161b22",    # Header background
    "row_even": "#0d1117",     # Even row background
    "row_odd": "#161b22",      # Odd row background
    "text": "#e6edf3",         # Main text color
    "text_muted": "#8b949e",   # Muted text
    "green": "#3fb950",        # Long/Profit
    "red": "#f85149",          # Short/Loss
    "border": "#30363d",       # Border color
    "accent": "#58a6ff",       # Accent color
}


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
        return f"{prefix}${abs_n / 1_000:.0f}K"
    return f"{prefix}${abs_n:.0f}"


def format_price(price: float) -> str:
    """Format price with appropriate precision."""
    if price >= 1000:
        return f"${price:,.0f}"
    if price >= 1:
        return f"${price:,.2f}"
    return f"${price:.4f}"


def strip_emojis(text: str) -> str:
    """Remove emojis and special unicode characters from text."""
    import re
    # Remove emojis and other special unicode
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002600-\U000026FF"  # misc symbols
        "\U0000200B-\U0000200D"  # zero width chars
        "\U0000FE0F"             # variation selector
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text).strip()


def truncate_label(label: str, max_len: int = 20) -> str:
    """Truncate label to fit, removing emojis first."""
    label = strip_emojis(label)
    if len(label) <= max_len:
        return label
    return label[:max_len - 1] + "..."


def format_address(address: str) -> str:
    """Format address as shortened hex."""
    if not address or len(address) < 10:
        return "unknown"
    return f"{address[:6]}...{address[-4:]}"


def generate_table_image(
    token: str,
    positions: list,
    output_path: Path,
    show_date: bool = True,
) -> Path:
    """Generate a styled table image for positions.

    Args:
        token: Token symbol (BTC, ETH, etc.)
        positions: List of position dictionaries
        output_path: Path to save the image
        show_date: Whether to show date in header

    Returns:
        Path to the generated image
    """
    # Prepare data
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
            truncate_label(label, 18) if label else "-",
            format_address(address),
            side,
            format_number(size),
            leverage,
            format_price(entry),
            format_price(mark),
            format_price(liq),
            format_number(upnl, include_sign=True),
        ])

    # Count longs/shorts
    longs = sum(1 for p in positions if p.get("side") == "Long")
    shorts = len(positions) - longs

    # Create figure
    fig_width = 16
    fig_height = 1.5 + len(rows) * 0.5
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])
    ax.axis('off')

    # Title
    date_str = datetime.now().strftime("%B %d, %Y")
    title = f"${token} Top {len(positions)} Positions"
    if show_date:
        title += f"  •  {date_str}"

    ax.text(0.5, 0.95, title, transform=ax.transAxes, fontsize=18, fontweight='bold',
            color=COLORS["text"], ha='center', va='top', fontfamily='monospace')

    # Subtitle with long/short counts (using colored text instead of emojis)
    ax.text(0.42, 0.88, f"{longs} Longs", transform=ax.transAxes, fontsize=12,
            color=COLORS["green"], ha='right', va='top', fontfamily='monospace', fontweight='bold')
    ax.text(0.5, 0.88, "  |  ", transform=ax.transAxes, fontsize=12,
            color=COLORS["text_muted"], ha='center', va='top', fontfamily='monospace')
    ax.text(0.58, 0.88, f"{shorts} Shorts", transform=ax.transAxes, fontsize=12,
            color=COLORS["red"], ha='left', va='top', fontfamily='monospace', fontweight='bold')

    # Column widths (proportional)
    col_widths = [0.03, 0.16, 0.12, 0.06, 0.09, 0.07, 0.10, 0.10, 0.12, 0.10]

    # Create table
    table = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc='center',
        loc='center',
        colWidths=col_widths,
        bbox=[0.02, 0.05, 0.96, 0.78]
    )

    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    for key, cell in table.get_celld().items():
        row, col = key
        cell.set_edgecolor(COLORS["border"])
        cell.set_linewidth(0.5)

        if row == 0:
            # Header row
            cell.set_facecolor(COLORS["header_bg"])
            cell.set_text_props(color=COLORS["accent"], fontweight='bold', fontfamily='monospace')
            cell.set_height(0.08)
        else:
            # Data rows
            bg_color = COLORS["row_even"] if row % 2 == 0 else COLORS["row_odd"]
            cell.set_facecolor(bg_color)
            cell.set_text_props(fontfamily='monospace')

            # Get the cell text to determine color
            text = cell.get_text().get_text()

            # Side column coloring
            if col == 3:  # Side column
                if text == "Long":
                    cell.set_text_props(color=COLORS["green"], fontweight='bold', fontfamily='monospace')
                elif text == "Short":
                    cell.set_text_props(color=COLORS["red"], fontweight='bold', fontfamily='monospace')
                else:
                    cell.set_text_props(color=COLORS["text"], fontfamily='monospace')
            # uPnL column coloring
            elif col == 9:  # uPnL column
                if text.startswith("+"):
                    cell.set_text_props(color=COLORS["green"], fontweight='bold', fontfamily='monospace')
                elif text.startswith("-"):
                    cell.set_text_props(color=COLORS["red"], fontweight='bold', fontfamily='monospace')
                else:
                    cell.set_text_props(color=COLORS["text"], fontfamily='monospace')
            else:
                cell.set_text_props(color=COLORS["text"], fontfamily='monospace')

    # Footer
    footer = "Data: Nansen  |  Powered by hyper-signals"
    ax.text(0.5, 0.01, footer, transform=ax.transAxes, fontsize=9,
            color=COLORS["text_muted"], ha='center', va='bottom', fontfamily='monospace')

    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor=COLORS["bg"],
                edgecolor='none', bbox_inches='tight', pad_inches=0.2)
    plt.close()

    return output_path


def main():
    """Main entry point."""
    # Read JSON from stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Generate images for each token
    generated = []
    tokens = ["BTC", "ETH", "SOL", "HYPE"]

    for i, token in enumerate(tokens):
        token_data = data.get(token, {})
        positions = []
        if isinstance(token_data, dict):
            positions = token_data.get("data", [])
        elif isinstance(token_data, list):
            positions = token_data

        if not positions:
            continue

        output_path = output_dir / f"{token.lower()}_positions.png"
        show_date = (i == 0)  # Only show date on first token

        generate_table_image(token, positions, output_path, show_date=show_date)
        generated.append(str(output_path))
        print(f"Generated: {output_path}", file=sys.stderr)

    # Output paths as JSON
    print(json.dumps({"images": generated}))


if __name__ == "__main__":
    main()
