# Nansen API - Perp Screener (Hyperliquid)

**Source:** https://docs.nansen.ai/api/hyperliquid/perp-screener
**Retrieved:** 2026-02-02
**Last Updated (source):** 3 months ago

---

## Overview

Discover and screen perpetual contracts on Hyperliquid with advanced filtering capabilities. This endpoint helps identify trending perpetual contracts, trading activity, funding rates, and smart money movements by combining metrics like volume, open interest, funding rates, and position data.

**What it helps to answer:**

1. Which perpetual contracts are experiencing significant trading volume and activity?
2. How do funding rates correlate with trading patterns and smart money positions?
3. What perpetual contracts show strong fundamentals in terms of open interest and trading patterns?
4. Which perpetual contracts are attracting smart money participation with long/short positions?

---

## Endpoint

```
POST https://api.nansen.ai/api/v1/perp-screener
```

---

## Authentication

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `apiKey` | string | Yes | API key for authentication |

---

## Request Body

**Content-Type:** `application/json`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | object (DateRange) | Yes | Date range for the perp screener |
| `pagination` | object (PaginationRequest) | No | Pagination parameters |
| `filters` | object (PerpScreenerFilters) | No | Additional filters to apply |
| `order_by` | array (SortOrder) | No | Custom sort order to override the endpoint's default ordering |

### Date Object

```json
{
  "from": "2025-10-01T00:00:00Z",
  "to": "2025-10-06T23:59:59Z"
}
```

### Pagination Object

```json
{
  "page": 1,
  "per_page": 10
}
```

### Filters Object

Example:
```json
{
  "token_symbol": "BTC",
  "volume": {
    "min": 10000
  }
}
```

Available filter options:
- `token_symbol` - Filter by token symbol
- `volume` - Filter by volume range (min/max)
- `buy_sell_pressure` - Filter by buy/sell pressure range
- `open_interest` - Filter by open interest range
- `smart_money_volume` - Filter by smart money volume (when `only_smart_money` is true)

### Order By

Examples:
- `[{"field": "volume", "direction": "DESC"}]` - Sort by volume descending
- `[{"field": "net_position_change", "direction": "DESC"}]` - Sort by net_position_change descending
- `[{"field": "buy_sell_pressure", "direction": "DESC"}]` - Sort by buy/sell pressure descending (smart money)

**Default behavior:**
- When `only_smart_money` is `false`: sorts by `buy_sell_pressure` DESC
- When `only_smart_money` is `true`: sorts by `net_position_change` DESC

---

## Common Scenarios

| Use Case | Required Parameters | Optional Filters | Expected Output |
|----------|---------------------|------------------|-----------------|
| Screen for perps with net buy/sell pressure and strong fundamentals | `date = { "from": "2025-10-01T00:00:00Z", "to": "2025-10-06T23:59:59Z" }` | `filters = { "buy_sell_pressure": { "min": 100000 }, "open_interest": { "min": 500000 } }` | Perps showing high buy/sell pressure and strong open interest, returned with mark price, volume, and trader details |
| Discover perps favored by smart money | `date = { "from": "2025-10-01T00:00:00Z", "to": "2025-10-06T23:59:59Z" }` | `only_smart_money = true`, `filters = { "smart_money_volume": { "min": 100000 } }` | Perps with the highest smart money volume, including smart money long/short counts, USD position sizes, and assets |

---

## Example Request

### HTTP

```http
POST /api/v1/perp-screener HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json
Accept: */*

{
  "date": {
    "from": "2025-10-01T00:00:00Z",
    "to": "2025-10-06T23:59:59Z"
  },
  "pagination": {
    "page": 1,
    "per_page": 10
  },
  "filters": {
    "token_symbol": "BTC",
    "volume": {
      "min": 10000
    }
  },
  "order_by": [
    {
      "direction": "DESC",
      "field": "buy_sell_pressure"
    }
  ]
}
```

### Python

```python
import requests

url = "https://api.nansen.ai/api/v1/perp-screener"
headers = {
    "apiKey": "YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "date": {
        "from": "2025-10-01T00:00:00Z",
        "to": "2025-10-06T23:59:59Z"
    },
    "pagination": {
        "page": 1,
        "per_page": 10
    },
    "filters": {
        "token_symbol": "BTC",
        "volume": {
            "min": 10000
        }
    },
    "order_by": [
        {
            "direction": "DESC",
            "field": "buy_sell_pressure"
        }
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

---

## Example Response

**Status:** 200 OK

```json
{
  "data": [
    {
      "buy_sell_pressure": 5518.4408,
      "buy_volume": 216502.59923,
      "funding": 0.0000125,
      "mark_price": 0.3301,
      "open_interest": 261310.461,
      "previous_price_usd": 0.4155,
      "sell_volume": 210984.15843,
      "token_symbol": "ARK",
      "trader_count": 109,
      "volume": 427486.75766
    },
    {
      "buy_sell_pressure": 25000,
      "buy_volume": 1250000,
      "funding": 0.0001,
      "mark_price": 45000,
      "open_interest": 5000000,
      "previous_price_usd": 44000,
      "sell_volume": 1250000,
      "token_symbol": "BTC",
      "trader_count": 500,
      "volume": 2500000
    },
    {
      "current_smart_money_position_longs_usd": 500000,
      "current_smart_money_position_shorts_usd": -500000,
      "funding": -0.0001,
      "mark_price": 3000,
      "net_position_change": 25000,
      "open_interest": 2000000,
      "previous_price_usd": 2900,
      "smart_money_buy_volume": 75000,
      "smart_money_longs_count": 5,
      "smart_money_sell_volume": 75000,
      "smart_money_shorts_count": 5,
      "smart_money_volume": 150000,
      "token_symbol": "ETH",
      "trader_count": 15
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "is_last_page": true
  }
}
```

---

## Response Fields

### Standard Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `token_symbol` | string | The perpetual contract token symbol |
| `buy_sell_pressure` | number | Net buy/sell pressure |
| `buy_volume` | number | Total buy volume |
| `sell_volume` | number | Total sell volume |
| `volume` | number | Total trading volume |
| `funding` | number | Current funding rate |
| `mark_price` | number | Current mark price |
| `open_interest` | number | Total open interest |
| `previous_price_usd` | number | Previous price in USD |
| `trader_count` | number | Number of traders |

### Smart Money Response Fields (when `only_smart_money` is true)

| Field | Type | Description |
|-------|------|-------------|
| `smart_money_volume` | number | Total smart money volume |
| `smart_money_buy_volume` | number | Smart money buy volume |
| `smart_money_sell_volume` | number | Smart money sell volume |
| `smart_money_longs_count` | number | Count of smart money long positions |
| `smart_money_shorts_count` | number | Count of smart money short positions |
| `current_smart_money_position_longs_usd` | number | Current smart money long positions in USD |
| `current_smart_money_position_shorts_usd` | number | Current smart money short positions in USD |
| `net_position_change` | number | Net position change |

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
| 500 | Internal Server Error - Server-side error |

---

## Related Endpoints

- [Hyperliquid Leaderboard](https://docs.nansen.ai/api/hyperliquid/hyperliquid-leaderboard)
- [Perp PnL Leaderboard](https://docs.nansen.ai/api/hyperliquid/perp-pnl-leaderboard)
