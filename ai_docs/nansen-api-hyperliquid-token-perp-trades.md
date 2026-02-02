# Nansen API - Hyperliquid Token Perp Trades

> **Source:** https://docs.nansen.ai/api/hyperliquid/token-perp-trades
> **Retrieved:** 2026-02-02
> **Last Updated:** ~2 months ago (per source)

---

## Get TGM Perp Trades Data

**Endpoint:** `POST https://api.nansen.ai/api/v1/tgm/perp-trades`

Retrieve perpetual trade data for a specific token on Hyperliquid. Shows individual trades with detailed information including trader address, trade side (Long/Short), action type (Add/Reduce/Open/Close), order type (Market/Limit), and trade metrics.

### Key Features

- Hyperliquid perpetual contracts only
- Smart money filtering capabilities
- Detailed trade breakdown with parsed action fields
- Support for both Long and Short position trading
- Market and Limit order types

---

## Authentication

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `apiKey` | string | Yes | API key for authentication (header) |

---

## Request Body

**Content-Type:** `application/json`

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `token_symbol` | string | Token symbol to fetch trades for | `"BTC"`, `"ETH"` |
| `date` | object (DateRange) | ISO 8601 date range with optional `from` and `to` fields | `{"from": "2025-07-07", "to": "2025-07-14"}` |

### Optional Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `pagination` | object (PaginationRequest) | Pagination parameters (`page`, `per_page`) | `{"page": 1, "per_page": 10}` |
| `filters` | object (TGMPerpTradesFilters) | Additional filters for side, action, order_type, etc. | `{"order_type": ["MARKET"], "side": ["Long"]}` |
| `order_by` | array (SortOrder) | Custom sort order to override default ordering | `[{"field": "block_timestamp", "direction": "DESC"}]` |

### Filter Options

The `filters` object supports:
- `order_type`: Array of order types (e.g., `["MARKET"]`, `["LIMIT"]`)
- `side`: Array of sides (e.g., `["Long"]`, `["Short"]`)
- Additional filter properties available

### Sort Order Options

Default sorting: `block_timestamp DESC, transaction_hash ASC, trader_address ASC` (ensures stable pagination and prevents duplicate rows)

Example sort orders:
- `[{"field": "block_timestamp", "direction": "DESC"}]` - Sort by timestamp descending
- `[{"field": "value_usd", "direction": "DESC"}]` - Sort by trade value descending

---

## Example Request

### HTTP

```http
POST /api/v1/tgm/perp-trades HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json
Accept: */*

{
  "token_symbol": "BTC",
  "date": {
    "from": "2025-07-07",
    "to": "2025-07-14"
  },
  "pagination": {
    "page": 1,
    "per_page": 10
  },
  "filters": {
    "order_type": ["MARKET"],
    "side": ["Long"]
  },
  "order_by": [
    {
      "field": "block_timestamp",
      "direction": "ASC"
    }
  ]
}
```

### Python

```python
import requests

url = "https://api.nansen.ai/api/v1/tgm/perp-trades"
headers = {
    "apiKey": "YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "token_symbol": "BTC",
    "date": {
        "from": "2025-07-07",
        "to": "2025-07-14"
    },
    "pagination": {
        "page": 1,
        "per_page": 10
    },
    "filters": {
        "order_type": ["MARKET"],
        "side": ["Long"]
    },
    "order_by": [
        {"field": "block_timestamp", "direction": "ASC"}
    ]
}

response = requests.post(url, headers=headers, json=payload)
data = response.json()
```

---

## Response

### Success Response (200)

**Content-Type:** `application/json`

```json
{
  "data": [
    {
      "trader_address_label": "Smart Money",
      "trader_address": "0x28c6c06298d514db089934071355e5743bf21d60",
      "token_symbol": "BTC",
      "side": "Long",
      "action": "Add",
      "token_amount": 1.5,
      "price_usd": 60000,
      "value_usd": 90000,
      "type": "MARKET",
      "block_timestamp": "2025-10-01T12:40:00Z",
      "transaction_hash": "0x61adb6da30853c5988f0204dd9f6e4abbc878e02c34030a4f707cf4ec3124bcb"
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
| `data` | array | List of perp trade records |
| `data[].trader_address_label` | string | Label for the trader (e.g., "Smart Money") |
| `data[].trader_address` | string | Ethereum address of the trader |
| `data[].token_symbol` | string | Token symbol (e.g., "BTC") |
| `data[].side` | string | Trade side: "Long" or "Short" |
| `data[].action` | string | Action type: "Add", "Reduce", "Open", "Close" |
| `data[].token_amount` | number | Amount of tokens traded |
| `data[].price_usd` | number | Price in USD at time of trade |
| `data[].value_usd` | number | Total trade value in USD |
| `data[].type` | string | Order type: "MARKET" or "LIMIT" |
| `data[].block_timestamp` | string | ISO 8601 timestamp of the trade |
| `data[].transaction_hash` | string | Transaction hash on the blockchain |
| `pagination` | object | Pagination metadata |
| `pagination.page` | number | Current page number |
| `pagination.per_page` | number | Items per page |
| `pagination.is_last_page` | boolean | Whether this is the last page |

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid request parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Content - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Related Endpoints

- [Token Perp Positions](https://docs.nansen.ai/api/hyperliquid/token-perp-positions) - Get perpetual position data
- [API Changelog](https://docs.nansen.ai/api/changelog) - API version history and updates
