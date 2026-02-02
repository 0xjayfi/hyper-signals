#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""Fetch top 10 perp positions for BTC, ETH, SOL, HYPE from Nansen API.

Usage:
    uv run scripts/fetch_positions.py
    uv run scripts/fetch_positions.py --tokens BTC,ETH
"""

import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

NANSEN_API_URL = "https://api.nansen.ai/api/v1/tgm/perp-positions"
DEFAULT_TOKENS = ["BTC", "ETH", "SOL", "HYPE"]
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds


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
            print(
                f"[WARN] Timeout fetching {token} (attempt {attempt + 1}/{max_retries})",
                file=sys.stderr,
            )

        except httpx.HTTPStatusError as e:
            last_error = e
            # Don't retry on 4xx client errors (except 429 rate limit)
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                print(
                    f"[ERROR] Client error fetching {token}: {e.response.status_code} - {e.response.text}",
                    file=sys.stderr,
                )
                raise

            print(
                f"[WARN] HTTP {e.response.status_code} fetching {token} (attempt {attempt + 1}/{max_retries})",
                file=sys.stderr,
            )

        except httpx.RequestError as e:
            last_error = e
            print(
                f"[WARN] Request error fetching {token} (attempt {attempt + 1}/{max_retries}): {e}",
                file=sys.stderr,
            )

        # Wait before retrying (exponential backoff)
        if attempt < max_retries - 1:
            print(f"[INFO] Retrying in {backoff:.1f}s...", file=sys.stderr)
            time.sleep(backoff)
            backoff *= 2  # Exponential backoff

    # All retries exhausted
    raise RuntimeError(f"Failed to fetch {token} after {max_retries} attempts") from last_error


def fetch_all_positions(tokens: list[str], api_key: str) -> dict:
    """Fetch positions for all specified tokens."""
    results = {}
    errors = []

    for token in tokens:
        try:
            print(f"[INFO] Fetching {token}...", file=sys.stderr)
            results[token] = fetch_positions_with_retry(token, api_key)
            print(f"[INFO] {token}: fetched {len(results[token].get('data', []))} positions", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to fetch {token}: {e}", file=sys.stderr)
            errors.append({"token": token, "error": str(e)})
            results[token] = {"data": [], "error": str(e)}

    if errors:
        print(f"[WARN] Completed with {len(errors)} error(s)", file=sys.stderr)

    return results


def parse_tokens_arg() -> list[str]:
    """Parse --tokens argument if provided."""
    for arg in sys.argv[1:]:
        if arg.startswith("--tokens="):
            tokens_str = arg.split("=", 1)[1]
            return [t.strip().upper() for t in tokens_str.split(",")]
    return DEFAULT_TOKENS


def main() -> int:
    # Load .env file from project root
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    # Get API key
    api_key = os.environ.get("NANSEN_API_KEY")
    if not api_key:
        print("[ERROR] NANSEN_API_KEY not set in environment or .env file", file=sys.stderr)
        return 1

    # Parse tokens
    tokens = parse_tokens_arg()
    print(f"[INFO] Fetching positions for: {', '.join(tokens)}", file=sys.stderr)

    # Fetch positions
    try:
        results = fetch_all_positions(tokens, api_key)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 1

    # Output JSON to stdout
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
