# Nansen Hyperliquid Leaderboard API

> **Source:** https://docs.nansen.ai/api/hyperliquid/hyperliquid-leaderboard
> **Retrieved:** 2026-02-02

---

## Common Scenarios

| Usecase | Required Parameters | Optional Filters | Expected Output |
|---------|---------------------|------------------|-----------------|
| Find top perpetual traders in a specific date range | `date = { "from": "2025-10-14", "to": "2025-10-15" }` | `pagination = { "page": 1, "per_page": 10 }` | List of the most profitable perpetual traders (addresses and labels) with their total PnL, ROI (%), and account values in the date range |
| Filter leaderboard for high-value profitable accounts | `date = { "from": "2025-10-14", "to": "2025-10-15" }` | `filters = { "account_value": { "min": 10000 }, "total_pnl": { "min": 1000 } }` | Leaderboard limited to traders with $10k+ account value and $1k+ profit, for easier benchmarking |
| Show only smart money leaders (filtered by trader address label) | `date = { "from": "2025-10-14", "to": "2025-10-15" }` | `filters = { "trader_address_label": "Smart Money" }` | Leaderboard showing only traders identified as Smart Money, with PnL, ROI, and account value for each |

---

## Get Perpetual Trading Leaderboard Data

**Method:** `POST`

**Endpoint:** `https://api.nansen.ai/api/v1/perp-leaderboard`

Get perpetual trading leaderboard data showing the most profitable traders within a given date range. This endpoint provides trader performance metrics including total PnL, ROI, and account values.

### What it helps to answer:

1. Who are the most profitable perpetual traders in a given timeframe?
2. What are the ROI percentages for top performing traders?
3. What are the account values of successful perpetual traders?
4. How do trader addresses and labels correlate with performance?

### Key Features:

- Trader address and label information
- Total PnL tracking in USD
- ROI calculations as percentages
- Account value tracking
- Flexible filtering and sorting options

---

## Authorization

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `apiKey` | string | Yes | API key for authentication |

---

## Request Body

**Content-Type:** `application/json`

Request model for Perp Leaderboard endpoint. This endpoint provides a perpetual trading leaderboard showing the most profitable traders within a given date range.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | object (DateOnlyRange) | **Required** | Date range object with optional `from` and `to` fields in `YYYY-MM-DD` format. Example: `{"from":"2025-10-14","to":"2025-10-15"}` |
| `pagination` | object (PaginationRequest) | Optional | Pagination parameters |
| `filters` | object (PerpLeaderboardFilters) | Optional | Additional filters to apply to the query. Example: `{"account_value":{"min":10000},"total_pnl":{"min":1000}}` |
| `order_by` | object (SortOrder) | Optional | Custom sort order to override the endpoint's default ordering |

### Date Object Properties

| Field | Type | Description |
|-------|------|-------------|
| `from` | string | Start date in `YYYY-MM-DD` format |
| `to` | string | End date in `YYYY-MM-DD` format |

### Pagination Object Properties

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Page number (starting from 1) |
| `per_page` | integer | Number of results per page |

### Filters Object Properties

| Field | Type | Description |
|-------|------|-------------|
| `account_value` | object | Filter by account value with `min` and/or `max` |
| `total_pnl` | object | Filter by total PnL with `min` and/or `max` |
| `trader_address_label` | string | Filter by trader label (e.g., "Smart Money") |

### Order By Object Properties

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field to sort by (e.g., `total_pnl`) |
| `direction` | string | Sort direction: `ASC` or `DESC` |

---

## Example Request

```http
POST /api/v1/perp-leaderboard HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json
Accept: */*

{
  "date": {
    "from": "2025-10-14",
    "to": "2025-10-15"
  },
  "pagination": {
    "page": 1,
    "per_page": 10
  },
  "filters": {
    "account_value": {
      "min": 10000
    },
    "total_pnl": {
      "min": 1000
    }
  },
  "order_by": [
    {
      "field": "total_pnl",
      "direction": "ASC"
    }
  ]
}
```

---

## Example Response

**Status:** `200 OK`

```json
{
  "data": [
    {
      "trader_address": "0x28c6c06298d514db089934071355e5743bf21d60",
      "trader_address_label": "Binance 14 [0x28c6c0]",
      "total_pnl": 1250.5,
      "roi": 15.5,
      "account_value": 10000
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
| `data` | array | Array of leaderboard records |
| `data[].trader_address` | string | Ethereum address of the trader |
| `data[].trader_address_label` | string | Human-readable label for the trader (e.g., exchange name) |
| `data[].total_pnl` | number | Total profit and loss in USD |
| `data[].roi` | number | Return on investment as a percentage |
| `data[].account_value` | number | Current account value in USD |
| `pagination` | object | Pagination metadata |
| `pagination.page` | integer | Current page number |
| `pagination.per_page` | integer | Results per page |
| `pagination.is_last_page` | boolean | Whether this is the last page of results |

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request - Invalid request parameters |
| `401` | Unauthorized - Invalid or missing API key |
| `403` | Forbidden - Access denied |
| `404` | Not Found - Endpoint or resource not found |
| `422` | Unprocessable Content - Validation error |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error - Server-side error |

---

## Related Endpoints

- [Address Perp Trades](https://docs.nansen.ai/api/hyperliquid/address-perp-trades)
- [Perp Screener](https://docs.nansen.ai/api/hyperliquid/perp-screener)
