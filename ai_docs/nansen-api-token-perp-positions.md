# Nansen API - Token Perp Positions

> **Source:** https://docs.nansen.ai/api/hyperliquid/token-perp-positions
> **Retrieved:** 2026-02-02
> **API Endpoint:** `POST https://api.nansen.ai/api/v1/tgm/perp-positions`

---

## Get TGM Perp Positions Data

Retrieve current perpetual positions for a specific token on Hyperliquid. Shows active positions with detailed metrics including entry price, mark price, leverage, PnL, and liquidation price.

### Key Features

- Hyperliquid perpetual contracts only (no chain field needed)
- Real-time position tracking with live PnL calculations
- Leverage and margin information
- Smart money filtering capabilities
- Support for both Long and Short positions

### What it helps to answer

1. What are the current perp positions for a specific token?
2. Which addresses have the largest positions by value?
3. What are the unrealized gains/losses on current positions?
4. What leverage levels are traders using?
5. Which smart money wallets are holding positions?

---

## Authentication

| Type | Header | Description |
|------|--------|-------------|
| ApiKeyAuth | `apiKey` | API key for authentication (Required) |

---

## Request Body

**Content-Type:** `application/json`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token_symbol` | string | **Required** | Token symbol (e.g., `BTC`) |
| `label_type` | enum | Optional | Label type filter. Default: `all_traders`. Possible values: `smart_money`, `all_traders`, `whale`, `public_figure` |
| `pagination` | object | Optional | Pagination parameters |
| `filters` | object | Optional | Additional filters to apply to the query |
| `order_by` | array | Optional | Custom sort order to override the endpoint's default ordering |

### Pagination Object

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `per_page` | integer | Number of results per page |

### Filters Object (TGMPerpPositionsFilters)

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_smart_money_labels` | array | Filter by smart money labels (e.g., `["Smart HL Perps Trader", "Fund"]`) |
| `position_value_usd` | object | Filter by position value in USD (e.g., `{"min": 10000}`) |
| `side` | array | Filter by position side (e.g., `["Long"]` or `["Short"]`) |
| `upnl_usd` | object | Filter by unrealized PnL in USD (e.g., `{"min": 0}`) |

### Order By Object (SortOrder)

| Parameter | Type | Description |
|-----------|------|-------------|
| `field` | string | Field to sort by. Options: `address`, `position_value_usd`, `upnl_usd`, `leverage` |
| `direction` | string | Sort direction: `ASC` or `DESC` |

---

## Example Request

```http
POST /api/v1/tgm/perp-positions HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json
Accept: */*

{
  "token_symbol": "BTC",
  "label_type": "all_traders",
  "pagination": {
    "page": 1,
    "per_page": 10
  },
  "filters": {
    "include_smart_money_labels": [
      "Smart HL Perps Trader",
      "Fund"
    ],
    "position_value_usd": {
      "min": 10000
    },
    "side": [
      "Long"
    ],
    "upnl_usd": {
      "min": 0
    }
  },
  "order_by": [
    {
      "field": "address",
      "direction": "ASC"
    }
  ]
}
```

---

## Response

### 200 - Success

**Content-Type:** `application/json`

```json
{
  "data": [
    {
      "address": "0x1234567890123456789012345678901234567890",
      "address_label": "Smart Money",
      "side": "Long",
      "position_value_usd": 50000,
      "position_size": 1.5,
      "leverage": "5X",
      "leverage_type": "cross",
      "entry_price": 50000,
      "mark_price": 50500,
      "liquidation_price": 45000,
      "funding_usd": 10.5,
      "upnl_usd": 500
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "is_last_page": true
  }
}
```

### Response Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `address` | string | Wallet address |
| `address_label` | string | Label associated with the address |
| `side` | string | Position side (`Long` or `Short`) |
| `position_value_usd` | number | Position value in USD |
| `position_size` | number | Position size in token units |
| `leverage` | string | Leverage used (e.g., `5X`) |
| `leverage_type` | string | Type of leverage (`cross` or `isolated`) |
| `entry_price` | number | Entry price |
| `mark_price` | number | Current mark price |
| `liquidation_price` | number | Liquidation price |
| `funding_usd` | number | Funding paid/received in USD |
| `upnl_usd` | number | Unrealized PnL in USD |

### Pagination Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Current page number |
| `per_page` | integer | Results per page |
| `is_last_page` | boolean | Whether this is the last page |

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Unprocessable Content |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

## Related Endpoints

- [Smart Money Perp Trades](https://docs.nansen.ai/api/hyperliquid/smart-money-perp-trades)
- [Token Perp Trades](https://docs.nansen.ai/api/hyperliquid/token-perp-trades)
