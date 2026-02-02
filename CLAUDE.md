# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hyper-Signals is an automated daily X (Twitter) feed orchestrator that posts threaded updates on the top 10 perpetual positions for BTC, ETH, SOL, and HYPE on Hyperliquid. It uses a modular pipeline architecture with three independent scripts that communicate via stdin/stdout JSON.

## Commands

```bash
# Run full pipeline (fetch → format → post)
uv run scripts/daily_feed.py

# Preview without posting
uv run scripts/daily_feed.py --dry-run

# Schedule post N minutes from now
uv run scripts/daily_feed.py --schedule=30

# Verify API connectivity
uv run scripts/daily_feed.py --health-check

# Run individual scripts
uv run scripts/fetch_positions.py              # Fetch positions (JSON to stdout)
uv run scripts/fetch_positions.py --tokens=BTC,ETH  # Specific tokens only

# Unix pipe composition
uv run scripts/fetch_positions.py | uv run scripts/format_thread.py | uv run scripts/post_typefully.py

# Run tests
uv run tests/test_pipeline.py
```

## Architecture

### Pipeline Flow
```
fetch_positions.py → format_thread.py → post_typefully.py
       ↓                    ↓                  ↓
   Nansen API          Transform          Typefully API
   (JSON out)          (JSON in/out)      (JSON in)
```

### Key Design Patterns

1. **UV Single-File Scripts**: Each script declares dependencies inline via PEP 723 (`# /// script` blocks). No virtualenv setup needed.

2. **Orchestrator Pattern**: `daily_feed.py` wraps all phases with unified error handling, logging, retry logic, and CLI argument parsing.

3. **Retry Strategy**: Exponential backoff (1s → 2s → 4s) with 3 max retries. Distinguishes retryable (5xx, 429) from fatal (4xx) errors.

4. **Stateless Design**: No database or cache. Each run is independent.

### External APIs

- **Nansen API v1**: `POST https://api.nansen.ai/api/v1/tgm/perp-positions` - Fetches perpetual position data
- **Typefully API v2**: `https://api.typefully.com/v2` - Creates/schedules Twitter drafts

### Environment Variables

Required in `.env`:
- `NANSEN_API_KEY` - Required for fetching position data
- `TYPEFULLY_API_KEY` - Required for posting (not needed for --dry-run)
- `TYPEFULLY_SOCIAL_SET_ID` - Optional, auto-discovered if omitted

## File Structure

- `scripts/daily_feed.py` - Main orchestrator entry point (478 lines)
- `scripts/fetch_positions.py` - Nansen API client
- `scripts/format_thread.py` - Pure data transformation (no dependencies)
- `scripts/post_typefully.py` - Typefully API client
- `tests/test_pipeline.py` - Integration tests with fixtures
- `specs/` - Detailed project specifications
- `ai_docs/` - Snapshots of Nansen and Typefully API documentation
