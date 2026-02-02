# Nansen API - Address Perp Positions

**Source:** https://docs.nansen.ai/api/hyperliquid/address-perp-positions
**Retrieved:** 2026-02-02

---

## Common Scenarios

| Usecase | Required Parameters | Optional Filters | Expected Output |
|---------|---------------------|------------------|-----------------|
| Check current perp positions for a single address | `address="0xa312114b5795dff9b8db50474dd57701aa78ad1e"` | `filters={"position_value_usd": {"min": 1000}}` | List of open perpetual positions with entry price, mark price, leverage, PnL, and margin info for the address |
| Get all perp positions with negative PnL for an address | `address="0xa312114b5795dff9b8db50474dd57701aa78ad1e"` | `filters={"unrealized_pnl_usd": {"max": 0}}` | List of positions with negative unrealized PnL |

---

## Get Perpetual Positions Data

**Endpoint:** `POST https://api.nansen.ai/api/v1/profiler/perp-positions`

Get perpetual positions data for a user by calling the Hyperliquid API directly. This endpoint provides real-time position information including entry price, mark price, PnL, leverage, and other position details.

### What it helps to answer:

1. What are the current perpetual positions for a specific user address?
2. What is the unrealized PnL and performance of each position?
3. What are the leverage levels and margin requirements for each position?
4. What are the liquidation prices and risk levels for each position?

---

## Authorization

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `apiKey` | string | Yes | API key for authentication (passed in header) |

---

## Request Body

**Content-Type:** `application/json`

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `address` | string (42 chars) | Yes | User's Hyperliquid address in 42-character hexadecimal format. Example: `0xa312114b5795dff9b8db50474dd57701aa78ad1e` |
| `filters` | object | No | Additional filters to apply to the query |
| `order_by` | array | No | Custom sort order to override the endpoint's default ordering |

### Filters Object (PerpPositionsFilters)

```json
{
  "position_value_usd": {
    "min": 1000
  },
  "unrealized_pnl_usd": {
    "max": 0
  }
}
```

### Order By Examples

- `[{"field": "position_value_usd", "direction": "DESC"}]` - Sort by position value descending
- `[{"field": "unrealized_pnl_usd", "direction": "ASC"}]` - Sort by unrealized PnL ascending

If not provided, positions are sorted by position value descending.

---

## Example Request

### HTTP

```http
POST /api/v1/profiler/perp-positions HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json
Accept: */*

{
  "address": "0xa312114b5795dff9b8db50474dd57701aa78ad1e",
  "filters": {
    "position_value_usd": {
      "min": 1000
    },
    "unrealized_pnl_usd": {
      "max": 0
    }
  },
  "order_by": [
    {
      "direction": "DESC",
      "field": "position_value_usd"
    }
  ]
}
```

### Python

```python
import requests

url = "https://api.nansen.ai/api/v1/profiler/perp-positions"
headers = {
    "apiKey": "YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "address": "0xa312114b5795dff9b8db50474dd57701aa78ad1e",
    "filters": {
        "position_value_usd": {"min": 1000},
        "unrealized_pnl_usd": {"max": 0}
    },
    "order_by": [
        {"direction": "DESC", "field": "position_value_usd"}
    ]
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

---

## Response

### Success Response (200)

**Content-Type:** `application/json`

```json
{
  "data": {
    "asset_positions": [
      {
        "position": {
          "cumulative_funding_all_time_usd": "-623.219722",
          "cumulative_funding_since_change_usd": "-618.925976",
          "cumulative_funding_since_open_usd": "-623.219722",
          "entry_price_usd": "0.43499",
          "leverage_type": "cross",
          "leverage_value": 3,
          "liquidation_price_usd": "66.817537196",
          "margin_used_usd": "1743.87343",
          "max_leverage_value": 3,
          "position_value_usd": "5231.62029",
          "return_on_equity": "2.2836393396",
          "size": "-50367.0",
          "token_symbol": "STBL",
          "unrealized_pnl_usd": "16677.54047"
        },
        "position_type": "oneWay"
      },
      {
        "position": {
          "cumulative_funding_all_time_usd": "200.361581",
          "cumulative_funding_since_change_usd": "201.157877",
          "cumulative_funding_since_open_usd": "200.361581",
          "entry_price_usd": "0.311285",
          "leverage_type": "cross",
          "leverage_value": 5,
          "liquidation_price_usd": "39.6872752647",
          "margin_used_usd": "2020.946984",
          "max_leverage_value": 5,
          "position_value_usd": "10104.73492",
          "return_on_equity": "3.1976362269",
          "size": "-90052.0",
          "token_symbol": "MOODENG",
          "unrealized_pnl_usd": "17927.1615"
        },
        "position_type": "oneWay"
      }
    ],
    "cross_maintenance_margin_used_usd": "722948.2832910001",
    "cross_margin_summary_account_value_usd": "4643143.4382309997",
    "cross_margin_summary_total_margin_used_usd": "1456365.231985",
    "cross_margin_summary_total_net_liquidation_position_on_usd": "13339928.690684",
    "cross_margin_summary_total_raw_usd": "13987445.0243870001",
    "margin_summary_account_value_usd": "4643143.4382309997",
    "margin_summary_total_margin_used_usd": "1456365.231985",
    "margin_summary_total_net_liquidation_position_usd": "13339928.690684",
    "margin_summary_total_raw_usd": "13987445.0243870001",
    "timestamp": 1761283435707,
    "withdrawable_usd": "2933647.2403759998"
  }
}
```

### Response Fields

#### Position Object

| Field | Type | Description |
|-------|------|-------------|
| `cumulative_funding_all_time_usd` | string | Total cumulative funding paid/received all time |
| `cumulative_funding_since_change_usd` | string | Cumulative funding since last position change |
| `cumulative_funding_since_open_usd` | string | Cumulative funding since position was opened |
| `entry_price_usd` | string | Entry price in USD |
| `leverage_type` | string | Type of leverage (e.g., "cross") |
| `leverage_value` | number | Current leverage multiplier |
| `liquidation_price_usd` | string | Price at which position would be liquidated |
| `margin_used_usd` | string | Margin used for this position in USD |
| `max_leverage_value` | number | Maximum allowed leverage |
| `position_value_usd` | string | Total position value in USD |
| `return_on_equity` | string | Return on equity ratio |
| `size` | string | Position size (negative = short, positive = long) |
| `token_symbol` | string | Token/asset symbol |
| `unrealized_pnl_usd` | string | Unrealized profit/loss in USD |

#### Account Summary Fields

| Field | Type | Description |
|-------|------|-------------|
| `cross_maintenance_margin_used_usd` | string | Cross maintenance margin used |
| `cross_margin_summary_account_value_usd` | string | Cross margin account value |
| `cross_margin_summary_total_margin_used_usd` | string | Total cross margin used |
| `cross_margin_summary_total_net_liquidation_position_on_usd` | string | Total net liquidation position |
| `cross_margin_summary_total_raw_usd` | string | Total raw USD value |
| `margin_summary_account_value_usd` | string | Total account value |
| `margin_summary_total_margin_used_usd` | string | Total margin used |
| `margin_summary_total_net_liquidation_position_usd` | string | Net liquidation position |
| `margin_summary_total_raw_usd` | string | Total raw USD |
| `timestamp` | number | Unix timestamp in milliseconds |
| `withdrawable_usd` | string | Available withdrawable amount in USD |

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

- [Hyperliquid Overview](https://docs.nansen.ai/api/hyperliquid)
- [Address Perp Trades](https://docs.nansen.ai/api/hyperliquid/address-perp-trades)
