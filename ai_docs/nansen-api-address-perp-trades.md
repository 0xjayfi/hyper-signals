# Nansen API - Address Perp Trades

> **Source:** https://docs.nansen.ai/api/hyperliquid/address-perp-trades
> **Retrieved:** 2026-02-02

## Overview

Get perpetual trade data for a user. This endpoint provides trade information including trade price, size, side, fees, and other trade details.

**What it helps to answer:**

1. What are the perpetual trades for a specific user address within a date range?
2. What are the trade prices, sizes, and directions for each trade?
3. What are the trading fees and closed PnL for each trade?
4. What are the order IDs and transaction hashes for trade tracking?

## Endpoint

```
POST https://api.nansen.ai/api/v1/profiler/perp-trades
```

## Authentication

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `apiKey` | string | Yes | API key for authentication |

## Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `address` | string (42 chars) | Yes | User's Hyperliquid address in 42-character hexadecimal format. Example: `0x45d26f28196d226497130c4bac709d808fed4029` |
| `date` | object | Yes | Date range for the trades. Example: `{"from": "2025-10-01", "to": "2025-10-10"}` |
| `filters` | object | No | Additional filters for the trades (see Filters section) |
| `pagination` | object | No | Pagination parameters (see Pagination section) |
| `order_by` | array | No | Sort order for the trades. Example: `[{"direction": "DESC", "field": "timestamp"}]` |

### Date Object

| Field | Type | Description |
|-------|------|-------------|
| `from` | string | Start date (YYYY-MM-DD format) |
| `to` | string | End date (YYYY-MM-DD format) |

### Filters Object (PerpTradeFilters)

Filters control which perpetual trades are included in the results based on various trade criteria.

| Field | Type | Description |
|-------|------|-------------|
| `size` | object | Filter by trade size. Example: `{"min": 0.001, "max": 1000}` |
| `value_usd` | object | Filter by USD value. Example: `{"min": 1000}` |
| `type` | string | Filter by trade direction: "Long" or "Short" |

### Pagination Object

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Page number (starts at 1) |
| `per_page` | integer | Number of results per page |

### Order By Object

| Field | Type | Description |
|-------|------|-------------|
| `direction` | string | Sort direction: "ASC" or "DESC" |
| `field` | string | Field to sort by (e.g., "timestamp", "closed_pnl") |

## Common Scenarios

### 1. Fetch all perp trades for an address within a specific date range

**Required Parameters:**
```json
{
  "address": "0x45d26f28196d226497130c4bac709d808fed4029",
  "date": {
    "from": "2025-10-01",
    "to": "2025-10-10"
  }
}
```

**Expected Output:** List of trades with timestamps, price, size, token, direction (Long/Short), action (Open/Close), and fees for the address.

### 2. Analyze high-value trades with closed PnL details

**Required Parameters:**
```json
{
  "address": "0x45d26f28196d226497130c4bac709d808fed4029",
  "date": {
    "from": "2025-10-01",
    "to": "2025-10-10"
  },
  "filters": {
    "value_usd": {
      "min": 1000
    }
  }
}
```

**Expected Output:** List of trades above $1,000 with closed PnL, fees paid, order IDs, and asset symbols.

### 3. Track all short trades and compare performance by token

**Required Parameters:**
```json
{
  "address": "0x45d26f28196d226497130c4bac709d808fed4029",
  "date": {
    "from": "2025-10-01",
    "to": "2025-10-10"
  },
  "filters": {
    "type": "Short"
  },
  "order_by": [
    {
      "direction": "DESC",
      "field": "closed_pnl"
    }
  ]
}
```

**Expected Output:** All short trades, sorted by closed profit, allowing analysis of which tokens and trades delivered the best results.

## Example Request

### HTTP

```http
POST /api/v1/profiler/perp-trades HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json
Accept: */*

{
  "address": "0x45d26f28196d226497130c4bac709d808fed4029",
  "date": {
    "from": "2025-10-01",
    "to": "2025-10-10"
  },
  "filters": {
    "size": {
      "max": 1000,
      "min": 0.001
    }
  },
  "pagination": {
    "page": 1,
    "per_page": 10
  },
  "order_by": [
    {
      "direction": "DESC",
      "field": "timestamp"
    }
  ]
}
```

### Python

```python
import requests

url = "https://api.nansen.ai/api/v1/profiler/perp-trades"
headers = {
    "apiKey": "YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "address": "0x45d26f28196d226497130c4bac709d808fed4029",
    "date": {
        "from": "2025-10-01",
        "to": "2025-10-10"
    },
    "filters": {
        "size": {
            "max": 1000,
            "min": 0.001
        }
    },
    "pagination": {
        "page": 1,
        "per_page": 10
    },
    "order_by": [
        {
            "direction": "DESC",
            "field": "timestamp"
        }
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

## Example Response

```json
{
  "pagination": {
    "page": 1,
    "per_page": 10,
    "is_last_page": true
  },
  "data": [
    {
      "action": "Add",
      "block_number": 756553592,
      "closed_pnl": 0,
      "crossed": true,
      "fee_token_symbol": "USDC",
      "fee_usd": 0.434851,
      "oid": 191284609448,
      "price": 0.25884,
      "side": "Short",
      "size": 6000,
      "start_position": -7788000,
      "timestamp": "2025-10-08T18:46:11.452000",
      "token_symbol": "DOGE",
      "transaction_hash": "0x50cea34e7464d3055248042d1817780203b600340f67f1d7f4974ea13368acef",
      "user": "0x45d26f28196d226497130c4bac709d808fed4029",
      "value_usd": 1553.04
    },
    {
      "action": "Open",
      "block_number": 756553593,
      "closed_pnl": 0,
      "crossed": false,
      "fee_token_symbol": "USDC",
      "fee_usd": 2.25,
      "oid": 191284609449,
      "price": 45000,
      "side": "Long",
      "size": 0.1,
      "start_position": 0,
      "timestamp": "2025-10-08T15:30:22.123000",
      "token_symbol": "BTC",
      "transaction_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
      "user": "0x45d26f28196d226497130c4bac709d808fed4029",
      "value_usd": 4500
    },
    {
      "action": "Close",
      "block_number": 756553594,
      "closed_pnl": 150,
      "crossed": true,
      "fee_token_symbol": "USDC",
      "fee_usd": 2.25,
      "oid": 191284609450,
      "price": 3000,
      "side": "Long",
      "size": 1.5,
      "start_position": 1000,
      "timestamp": "2025-10-08T12:15:33.789000",
      "token_symbol": "ETH",
      "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
      "user": "0x45d26f28196d226497130c4bac709d808fed4029",
      "value_usd": 4500
    }
  ]
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `action` | string | Trade action: "Open", "Close", or "Add" |
| `block_number` | integer | Block number of the transaction |
| `closed_pnl` | number | Realized profit/loss from the trade |
| `crossed` | boolean | Whether the trade crossed the spread |
| `fee_token_symbol` | string | Token used for fees (e.g., "USDC") |
| `fee_usd` | number | Trading fee in USD |
| `oid` | integer | Order ID |
| `price` | number | Trade execution price |
| `side` | string | Trade direction: "Long" or "Short" |
| `size` | number | Trade size in base asset |
| `start_position` | number | Position size before trade |
| `timestamp` | string | ISO 8601 timestamp of the trade |
| `token_symbol` | string | Trading pair symbol (e.g., "BTC", "ETH", "DOGE") |
| `transaction_hash` | string | Blockchain transaction hash |
| `user` | string | User's wallet address |
| `value_usd` | number | Trade value in USD |

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Content - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Related Endpoints

- [Address Perp Positions](https://docs.nansen.ai/api/hyperliquid/address-perp-positions)
- [Hyperliquid Leaderboard](https://docs.nansen.ai/api/hyperliquid/hyperliquid-leaderboard)
