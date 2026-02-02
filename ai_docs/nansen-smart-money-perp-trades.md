# Nansen API - Smart Money Perp Trades

**Source:** https://docs.nansen.ai/api/hyperliquid/smart-money-perp-trades
**Retrieved:** 2026-02-02

---

## Get Smart Money Perpetual Trades Data

**Method:** POST
**Endpoint:** `https://api.nansen.ai/api/v1/smart-money/perp-trades`

Access real-time perpetual trading activity from smart traders and funds on Hyperliquid. This endpoint provides granular transaction-level data showing exactly what sophisticated traders are trading on perpetual contracts.

### Key Features

- Hyperliquid perpetual contracts only (no chain field needed)
- Real-time trading data from smart money wallets
- Detailed trade information including coin, amount, price, action, and type
- Smart money filtering capabilities
- Type filtering (Market/Limit)
- Only new positions filter to show only position opening trades (defaults to false - shows all trades)

---

## Authentication

### ApiKeyAuth

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `apiKey` | string | Yes | API key for authentication |

---

## Request Body

**Content-Type:** `application/json`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filters` | object (SmartMoneyPerpTradesFilters) | Optional | Additional filters to apply. Only filters for columns that are being selected will be applied. |
| `only_new_positions` | boolean | Optional | When True, includes 'Open' position actions (Open Long, Open Short). Can be combined with other action filters using OR logic (union). When False (default), returns all trades. Default: `false` |
| `pagination` | object (PaginationRequest) | Optional | Pagination parameters |
| `order_by` | object (SortOrder) | Optional | Custom sort order to override the endpoint's default ordering. |

### Filter Example

```json
{
  "action": "Buy - Add Long",
  "side": "Long",
  "token_symbol": "BTC",
  "type": "Limit",
  "value_usd": {
    "max": 10000,
    "min": 1000
  }
}
```

### Order By Examples

- `[{"field": "value_usd", "direction": "DESC"}]` - Sort by trade value descending
- `[{"field": "block_timestamp", "direction": "ASC"}]` - Sort by timestamp ascending
- `[{"field": "token_amount", "direction": "DESC"}, {"field": "block_timestamp", "direction": "ASC"}]` - Sort by token amount descending, then timestamp ascending

---

## Example Request

### HTTP

```http
POST /api/v1/smart-money/perp-trades HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json
Accept: */*
Content-Length: 249

{
  "filters": {
    "action": "Buy - Add Long",
    "side": "Long",
    "token_symbol": "BTC",
    "type": "Limit",
    "value_usd": {
      "max": 10000,
      "min": 1000
    }
  },
  "only_new_positions": true,
  "pagination": {
    "page": 1,
    "per_page": 10
  },
  "order_by": [
    {
      "field": "block_timestamp",
      "direction": "ASC"
    }
  ]
}
```

---

## Responses

### 200 - Smart money perpetual trades data

**Content-Type:** `application/json`

**Response Model:** `SmartMoneyPerpTradesResponse`

Response model for smart money perpetual trades endpoint. Contains the filtered smart money perpetual trades data with metadata.

#### Example Response

```json
{
  "data": [
    {
      "trader_address_label": "text",
      "trader_address": "text",
      "token_symbol": "text",
      "side": "Long",
      "action": "Add",
      "token_amount": 1,
      "price_usd": 1,
      "value_usd": 1,
      "type": "Market",
      "block_timestamp": "text",
      "transaction_hash": "text"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "is_last_page": true
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `trader_address_label` | string | Label/name for the trader address |
| `trader_address` | string | Wallet address of the trader |
| `token_symbol` | string | Symbol of the token being traded |
| `side` | string | Position side: "Long" or "Short" |
| `action` | string | Trade action (e.g., "Add", "Open", "Close") |
| `token_amount` | number | Amount of tokens traded |
| `price_usd` | number | Price in USD |
| `value_usd` | number | Total value of the trade in USD |
| `type` | string | Order type: "Market" or "Limit" |
| `block_timestamp` | string | Timestamp of the trade |
| `transaction_hash` | string | Transaction hash |

#### Pagination Fields

| Field | Type | Description |
|-------|------|-------------|
| `page` | number | Current page number |
| `per_page` | number | Number of items per page |
| `is_last_page` | boolean | Whether this is the last page |

### Error Responses

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

- [Perp PnL Leaderboard](https://docs.nansen.ai/api/hyperliquid/perp-pnl-leaderboard)
- [Token Perp Positions](https://docs.nansen.ai/api/hyperliquid/token-perp-positions)
