# Nansen API - Perp PnL Leaderboard

**Source:** https://docs.nansen.ai/api/hyperliquid/perp-pnl-leaderboard
**Retrieved:** 2026-02-02
**API Endpoint:** `POST https://api.nansen.ai/api/v1/tgm/perp-pnl-leaderboard`

---

## Overview

Rank traders by their profit/loss performance for a specific perpetual contract on Hyperliquid. Shows both realized profits (from completed trades) and unrealized profits (from current holdings), along with ROI percentages and trading patterns. This endpoint can be used to analyze the realized and unrealized profit for each trader who traded the input perpetual contract.

### Key Features

- Hyperliquid perpetual contracts only (no chain field needed)
- Realized and unrealized PnL tracking
- ROI calculations and trading patterns
- Position size and balance tracking

---

## Authentication

| Type | Header | Description |
|------|--------|-------------|
| ApiKeyAuth | `apiKey` | API key for authentication (required) |

---

## Request Format

**Content-Type:** `application/json`

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `token_symbol` | string | Perpetual contract symbol (e.g., BTC, ETH, SOL) | `"BTC"` |
| `date` | object | ISO 8601 date range object with `from` and `to` fields | `{"from": "2025-10-14", "to": "2025-10-15"}` |

### Optional Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `pagination` | object | Pagination parameters with `page` and `per_page` | `{"page": 1, "per_page": 10}` |
| `filters` | object | Additional filters (see Filters section) | See below |
| `order_by` | array | Custom sort order | `[{"field": "pnl_usd_realised", "direction": "ASC"}]` |

### Filters (TGMPerpPnlLeaderboardFilters)

| Filter | Type | Description |
|--------|------|-------------|
| `pnl_usd_realised` | object | Filter by realized PnL range (`min`, `max`) |
| `position_value_usd` | object | Filter by position value range (`min`, `max`) |
| `trader_address_label` | string | Filter by trader label (e.g., "Smart Money") |

---

## Common Scenarios

### 1. Filter for High-Profit and High-Balance Addresses

```json
{
  "token_symbol": "ETH",
  "date": {
    "from": "2025-10-14",
    "to": "2025-10-15"
  },
  "filters": {
    "pnl_usd_realised": { "min": 100000 },
    "position_value_usd": { "min": 100000 }
  }
}
```

**Expected Output:** Only addresses with at least $100k realized PnL and $100k+ in position value are shown.

### 2. Surface Only Smart Money Traders for a Specific Contract

```json
{
  "token_symbol": "SOL",
  "date": {
    "from": "2025-10-14",
    "to": "2025-10-15"
  },
  "filters": {
    "trader_address_label": "Smart Money"
  }
}
```

**Expected Output:** Leaderboard limited to traders labeled as Smart Money.

---

## Example Request

### HTTP

```http
POST /api/v1/tgm/perp-pnl-leaderboard HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json
Accept: */*

{
  "token_symbol": "BTC",
  "date": {
    "from": "2025-10-14",
    "to": "2025-10-15"
  },
  "pagination": {
    "page": 1,
    "per_page": 10
  },
  "filters": {
    "pnl_usd_realised": {
      "min": 1000
    },
    "position_value_usd": {
      "min": 1000
    }
  },
  "order_by": [
    {
      "field": "pnl_usd_realised",
      "direction": "ASC"
    }
  ]
}
```

### Python

```python
import requests

url = "https://api.nansen.ai/api/v1/tgm/perp-pnl-leaderboard"
headers = {
    "apiKey": "YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "token_symbol": "BTC",
    "date": {
        "from": "2025-10-14",
        "to": "2025-10-15"
    },
    "pagination": {
        "page": 1,
        "per_page": 10
    },
    "filters": {
        "pnl_usd_realised": {"min": 1000},
        "position_value_usd": {"min": 1000}
    },
    "order_by": [
        {"field": "pnl_usd_realised", "direction": "ASC"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()
```

---

## Response Format

### Success Response (200)

```json
{
  "data": [
    {
      "trader_address": "0x28c6c06298d514db089934071355e5743bf21d60",
      "trader_address_label": "Binance 14 [0x28c6c0]",
      "price_usd": 1.23,
      "pnl_usd_realised": 1250.5,
      "pnl_usd_unrealised": 100.25,
      "holding_amount": 5000,
      "position_value_usd": 6000,
      "max_balance_held": 10000,
      "max_balance_held_usd": 12000,
      "still_holding_balance_ratio": 0.5,
      "netflow_amount_usd": 2500.75,
      "netflow_amount": 1500,
      "roi_percent_total": 15.5,
      "roi_percent_realised": 12.3,
      "roi_percent_unrealised": 3.2,
      "pnl_usd_total": 1350.75,
      "nof_trades": 25
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "is_last_page": true
  }
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `trader_address` | string | Wallet address of the trader |
| `trader_address_label` | string | Human-readable label for the address |
| `price_usd` | number | Current price in USD |
| `pnl_usd_realised` | number | Realized profit/loss in USD |
| `pnl_usd_unrealised` | number | Unrealized profit/loss in USD |
| `holding_amount` | number | Current holding amount |
| `position_value_usd` | number | Current position value in USD |
| `max_balance_held` | number | Maximum balance ever held |
| `max_balance_held_usd` | number | Maximum balance in USD |
| `still_holding_balance_ratio` | number | Ratio of current to max holdings |
| `netflow_amount_usd` | number | Net flow amount in USD |
| `netflow_amount` | number | Net flow amount |
| `roi_percent_total` | number | Total ROI percentage |
| `roi_percent_realised` | number | Realized ROI percentage |
| `roi_percent_unrealised` | number | Unrealized ROI percentage |
| `pnl_usd_total` | number | Total PnL in USD |
| `nof_trades` | number | Number of trades |

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid request format |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Content - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Related Endpoints

- [Perp Screener](https://docs.nansen.ai/api/hyperliquid/perp-screener)
- [Smart Money Perp Trades](https://docs.nansen.ai/api/hyperliquid/smart-money-perp-trades)
