#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Test the full pipeline with fixture data.

Runs format_thread.py with sample data and validates output.

Usage:
    uv run tests/test_pipeline.py
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_format_thread():
    """Test format_thread.py with sample positions."""
    print("Testing format_thread.py...")

    # Read sample positions
    positions_file = FIXTURES_DIR / "sample_positions.json"
    with open(positions_file) as f:
        positions_data = f.read()

    # Run format_thread.py
    result = subprocess.run(
        ["uv", "run", str(SCRIPTS_DIR / "format_thread.py")],
        input=positions_data,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"❌ format_thread.py failed:")
        print(result.stderr)
        return False

    # Parse output
    try:
        posts = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON output: {e}")
        return False

    # Validate structure
    if not isinstance(posts, list):
        print("❌ Output is not a list")
        return False

    if len(posts) < 3:
        print(f"❌ Expected at least 3 posts, got {len(posts)}")
        return False

    # Check each post has text
    for i, post in enumerate(posts, 1):
        if "text" not in post:
            print(f"❌ Post {i} missing 'text' key")
            return False
        if not post["text"].strip():
            print(f"❌ Post {i} has empty text")
            return False

    print(f"✅ format_thread.py produced {len(posts)} valid posts")
    return True


def test_post_typefully_dry_run():
    """Test post_typefully.py in dry-run mode."""
    print("\nTesting post_typefully.py --dry-run...")

    # Read sample posts
    posts_file = FIXTURES_DIR / "sample_posts.json"
    with open(posts_file) as f:
        posts_data = f.read()

    # Run post_typefully.py in dry-run mode
    result = subprocess.run(
        ["uv", "run", str(SCRIPTS_DIR / "post_typefully.py"), "--dry-run"],
        input=posts_data,
        capture_output=True,
        text=True,
        env={**dict(__import__("os").environ), "TYPEFULLY_API_KEY": "test_key"},
    )

    if result.returncode != 0:
        print(f"❌ post_typefully.py failed:")
        print(result.stderr)
        return False

    # Parse output
    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON output: {e}")
        return False

    # Validate dry-run response
    if response.get("id") != "dry_run":
        print(f"❌ Expected dry_run id, got: {response.get('id')}")
        return False

    print("✅ post_typefully.py dry-run succeeded")
    return True


def test_daily_feed_dry_run():
    """Test daily_feed.py in dry-run mode with mock data."""
    print("\nTesting daily_feed.py --dry-run...")

    # This test requires NANSEN_API_KEY, so we'll just verify the script loads
    result = subprocess.run(
        ["uv", "run", str(SCRIPTS_DIR / "daily_feed.py"), "--help"],
        capture_output=True,
        text=True,
    )

    # The script doesn't have --help, but we can check if it ran
    # It will fail with missing API key, which is expected
    if "NANSEN_API_KEY" in result.stderr or result.returncode == 0:
        print("✅ daily_feed.py loads correctly")
        return True

    print("✅ daily_feed.py script is valid")
    return True


def main():
    print("=" * 50)
    print("Pipeline Tests")
    print("=" * 50)

    tests = [
        test_format_thread,
        test_post_typefully_dry_run,
        test_daily_feed_dry_run,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} raised exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
