#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///
"""Post a thread to X and Threads via Typefully API v2.

Usage:
    cat posts.json | uv run scripts/post_typefully.py [--dry-run] [--schedule=N]

Options:
    --dry-run       Preview the draft without posting
    --schedule=N    Schedule post N minutes from now

Environment:
    TYPEFULLY_API_KEY       Required. Your Typefully API key
    TYPEFULLY_SOCIAL_SET_ID Optional. Social set ID (auto-discovered if not set)
"""

import httpx
import json
import os
import sys
from datetime import datetime, timedelta, timezone

TYPEFULLY_API_URL = "https://api.typefully.com/v2"


def get_headers(api_key: str) -> dict:
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
            headers=get_headers(api_key),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["results"]


def create_draft(
    api_key: str,
    social_set_id: int,
    posts: list[dict],
    schedule_minutes: int | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a draft/thread on Typefully for X and Threads."""
    payload = {
        "platforms": {
            "x": {
                "enabled": True,
                "posts": posts,
            },
            "threads": {
                "enabled": True,
                "posts": posts,
            },
        },
        "draft_title": f"Hyperliquid Daily Positions - {datetime.now().strftime('%Y-%m-%d')}",
        "share": True,
    }

    # Schedule for later if specified
    if schedule_minutes:
        publish_at = datetime.now(timezone.utc) + timedelta(minutes=schedule_minutes)
        payload["publish_at"] = publish_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    if dry_run:
        print("[DRY RUN] Would create draft with payload:", file=sys.stderr)
        print(json.dumps(payload, indent=2), file=sys.stderr)
        return {"id": "dry_run", "status": "draft", "posts_count": len(posts)}

    with httpx.Client() as client:
        response = client.post(
            f"{TYPEFULLY_API_URL}/social-sets/{social_set_id}/drafts",
            headers=get_headers(api_key),
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


def parse_args() -> tuple[bool, int | None]:
    """Parse command line arguments."""
    dry_run = "--dry-run" in sys.argv
    schedule_minutes = None

    for arg in sys.argv[1:]:
        if arg.startswith("--schedule="):
            try:
                schedule_minutes = int(arg.split("=")[1])
            except (ValueError, IndexError):
                print(f"Error: Invalid schedule value: {arg}", file=sys.stderr)
                sys.exit(1)

    return dry_run, schedule_minutes


def main():
    dry_run, schedule_minutes = parse_args()

    # Get API key
    api_key = os.environ.get("TYPEFULLY_API_KEY")
    if not api_key:
        print("Error: TYPEFULLY_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Get or auto-discover social set ID
    social_set_id = os.environ.get("TYPEFULLY_SOCIAL_SET_ID")

    if not social_set_id:
        if dry_run:
            print("[DRY RUN] Would auto-discover social set", file=sys.stderr)
            social_set_id = "0"
        else:
            # Auto-discover first social set
            print("Auto-discovering social set...", file=sys.stderr)
            social_sets = get_social_sets(api_key)
            if not social_sets:
                print("Error: No social sets found. Connect an account at typefully.com", file=sys.stderr)
                sys.exit(1)
            social_set = social_sets[0]
            social_set_id = str(social_set["id"])
            print(f"Using social set: {social_set.get('username', 'unknown')} (ID: {social_set_id})", file=sys.stderr)

    # Read posts from stdin
    try:
        posts = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(posts, list):
        print("Error: Expected JSON array of posts", file=sys.stderr)
        sys.exit(1)

    if not posts:
        print("Error: Posts array is empty", file=sys.stderr)
        sys.exit(1)

    # Log what we're doing
    action = "Creating draft" if not schedule_minutes else f"Scheduling draft ({schedule_minutes} min)"
    print(f"{action} with {len(posts)} posts...", file=sys.stderr)

    # Create the draft
    result = create_draft(
        api_key=api_key,
        social_set_id=int(social_set_id),
        posts=posts,
        schedule_minutes=schedule_minutes,
        dry_run=dry_run,
    )

    # Output result
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
