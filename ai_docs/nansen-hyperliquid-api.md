# Nansen Hyperliquid API Documentation

> **Source:** https://docs.nansen.ai/api/hyperliquid
> **Retrieved:** 2026-02-02
> **Base URL:** https://api.nansen.ai

---

## Overview

Nansen's Hyperliquid API endpoints provide comprehensive access to perp trading data on Hyperliquid. Track positions, analyze trades, screen tokens, and follow smart money activity across the fastest-growing perps platform.

## What can you do?

With Hyperliquid endpoints, you can:

- **Track wallet positions:** Monitor real-time perpetual positions, PnL, and account health
- **Analyze trading activity:** View detailed trade history and execution data of any address
- **Screen perp trading activity:** Find high-volume tokens and smart money flows on Hyperliquid
- **Find top performers:** Discover the most profitable traders on specific tokens.

## Available Endpoints

| Use Case | Endpoint | Best For |
|----------|----------|----------|
| See all open positions for a wallet including leverage, PnL, and liquidation prices | Address Perp Positions | Snapshot of current positions |
| View a wallet's trading history with entry/exit prices, fees, and PnL | Address Perp Trades | Trade by trade breakdown of address activity |
| See top profitable wallets on Hyperliquid over a given period | Hyperliquid Leaderboard | Find profitable wallets and copy trading |
| Find high-volume perp tokens or see where smart money is trading | Perp Screener | Market discovery & trends |
| Find the most profitable traders on a specific perp token | Perp PnL Leaderboard | Performance rankings |
| Track what smart money wallets are trading on Hyperliquid | Smart Money Perp Trades | Real-time smart money |
| See all open positions for a specific perp token including leverage, PnL, and liquidation prices | Token Perp Positions | Snapshot of current positions for a token |
| View trading history for a specific perp token over a time period | Token Perp Trades | All trading activity for a specific token |

## Key Differences: Hyperliquid vs. Other Chains

### Token Identification

**Important**: Hyperliquid perp endpoints use **token symbols** instead of token addresses in Token God Mode Inputs

| Other Chains | Hyperliquid |
|--------------|-------------|
| `token_address: "0x1234..."` | `token_symbol: "BTC"` |
| Use contract addresses | Use ticker symbols (BTC, ETH, SOL, etc.) |

**Example:**
```json
// Other chains
{"token_address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"}

// Hyperliquid
{"token_symbol": "BTC"}  // For leaderboard endpoint
```

### Positive and Negative Positions

Some endpoints (e.g., Token Perp Positions) have negative Position value. This usually represents a short and a positive value represents a long.

## Quick Start Checklist

1. **Get your API key** from Nansen
2. **Choose your use case:**
   - Wallet monitoring → Use `/perp-positions` + `/perp-trades`
   - Market discovery → Use `/perp-screener`
   - Copy trading → Use `/perp-leaderboard` + `/tgm/perp-pnl-leaderboard`
3. **Remember**: Use token symbols (BTC, ETH) not addresses
4. **Add filters**: Refine results with volume, PnL, or time filters

---

## API Authentication

All endpoints require API key authentication via the `apiKey` header.

```
apiKey: YOUR_API_KEY
```

---

## 1. Address Perp Positions

**Endpoint:** `POST https://api.nansen.ai/api/v1/profiler/perp-positions`

Get perpetual positions data for a user by calling the Hyperliquid API directly. This endpoint provides real-time position information including entry price, mark price, PnL, leverage, and other position details.

### What it helps to answer:

1. What are the current perpetual positions for a specific user address?
2. What is the unrealized PnL and performance of each position?
3. What are the leverage levels and margin requirements for each position?
4. What are the liquidation prices and risk levels for each position?

### Common Scenarios

| Usecase | Required Parameters | Optional Filters | Expected Output |
|---------|---------------------|------------------|-----------------|
| Check current perp positions for a single address | `address="0xa312114b5795dff9b8db50474dd57701aa78ad1e"` | `filters={"position_value_usd": {"min": 1000}}` | List of open perpetual positions with entry price, mark price, leverage, PnL, and margin info for the address |
| Get all perp positions with negative PnL for an address | `address="0xa312114b5795dff9b8db50474dd57701aa78ad1e"` | `filters={"unrealized_pnl_usd": {"max": 0}}` | List of positions with negative unrealized PnL |

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `address` | string (42 chars) | Yes | User's Hyperliquid address in 42-character hexadecimal format |
| `filters` | object | No | Additional filters to apply (see Filters section) |
| `order_by` | array | No | Custom sort order (e.g., `[{"field": "position_value_usd", "direction": "DESC"}]`) |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| `position_value_usd` | `{"min": number, "max": number}` | Filter by position value in USD |
| `unrealized_pnl_usd` | `{"min": number, "max": number}` | Filter by unrealized PnL |

### Example Request

```http
POST /api/v1/profiler/perp-positions HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json

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

### Example Response

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

---

## 2. Address Perp Trades

**Endpoint:** `POST https://api.nansen.ai/api/v1/profiler/perp-trades`

Get perpetual trade data for a user. This endpoint provides trade information including trade price, size, side, fees, and other trade details.

### What it helps to answer:

1. What are the perpetual trades for a specific user address within a date range?
2. What are the trade prices, sizes, and directions for each trade?
3. What are the trading fees and closed PnL for each trade?
4. What are the order IDs and transaction hashes for trade tracking?

### Common Scenarios

| Usecase | Required Parameters | Optional Filters | Expected Output |
|---------|---------------------|------------------|-----------------|
| Fetch all perp trades for an address within a specific date range | `address="0x45d26f28196d226497130c4bac709d808fed4029"` `date={"from": "2025-10-01", "to": "2025-10-10"}` | (none needed for basic usage) | List of trades with timestamps, price, size, token, direction (Long/Short), action (Open/Close), and fees |
| Analyze high-value trades with closed PnL details | `address="0x45d26f28196d226497130c4bac709d808fed4029"` `date={"from": "2025-10-01", "to": "2025-10-10"}` | `filters={"value_usd": {"min": 1000}}` | List of trades above $1,000 with closed PnL, fees paid, order IDs, and asset symbols |
| Track all short trades and compare performance by token | `address="0x45d26f28196d226497130c4bac709d808fed4029"` `date={"from": "2025-10-01", "to": "2025-10-10"}` | `filters={"type": "Short"}` `order_by=[{"direction": "DESC", "field": "closed_pnl"}]` | All short trades, sorted by closed profit |

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `address` | string (42 chars) | Yes | User's Hyperliquid address |
| `date` | object | Yes | Date range (`{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}`) |
| `filters` | object | No | Additional filters |
| `pagination` | object | No | Page and per_page parameters |
| `order_by` | array | No | Custom sort order |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| `size` | `{"min": number, "max": number}` | Filter by trade size |
| `value_usd` | `{"min": number, "max": number}` | Filter by trade value in USD |
| `type` | string | Filter by trade type ("Long" or "Short") |

### Example Request

```http
POST /api/v1/profiler/perp-trades HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json

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

### Example Response

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
    }
  ]
}
```

---

## 3. Hyperliquid Leaderboard

**Endpoint:** `POST https://api.nansen.ai/api/v1/perp-leaderboard`

Get perpetual trading leaderboard data showing the most profitable traders within a given date range.

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

### Common Scenarios

| Usecase | Required Parameters | Optional Filters | Expected Output |
|---------|---------------------|------------------|-----------------|
| Find top perpetual traders in a specific date range | `date={"from": "2025-10-14", "to": "2025-10-15"}` | `pagination={"page": 1, "per_page": 10}` | List of the most profitable perpetual traders with total PnL, ROI (%), and account values |
| Filter leaderboard for high-value profitable accounts | `date={"from": "2025-10-14", "to": "2025-10-15"}` | `filters={"account_value": {"min": 10000}, "total_pnl": {"min": 1000}}` | Traders with $10k+ account value and $1k+ profit |
| Show only smart money leaders | `date={"from": "2025-10-14", "to": "2025-10-15"}` | `filters={"trader_address_label": "Smart Money"}` | Leaderboard showing only Smart Money traders |

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | object | Yes | Date range in YYYY-MM-DD format |
| `pagination` | object | No | Page and per_page parameters |
| `filters` | object | No | Additional filters |
| `order_by` | array | No | Custom sort order |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| `account_value` | `{"min": number, "max": number}` | Filter by account value |
| `total_pnl` | `{"min": number, "max": number}` | Filter by total PnL |
| `trader_address_label` | string | Filter by trader label |

### Example Request

```http
POST /api/v1/perp-leaderboard HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json

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
      "direction": "DESC"
    }
  ]
}
```

### Example Response

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

---

## 4. Perp Screener

**Endpoint:** `POST https://api.nansen.ai/api/v1/perp-screener`

Discover and screen perpetual contracts on Hyperliquid with advanced filtering capabilities. This endpoint helps identify trending perpetual contracts, trading activity, funding rates, and smart money movements.

### What it helps to answer:

1. Which perpetual contracts are experiencing significant trading volume and activity?
2. How do funding rates correlate with trading patterns and smart money positions?
3. What perpetual contracts show strong fundamentals in terms of open interest and trading patterns?
4. Which perpetual contracts are attracting smart money participation with long/short positions?

### Common Scenarios

| Usecase | Required Parameters | Optional Filters | Expected Output |
|---------|---------------------|------------------|-----------------|
| Screen for perps with net buy/sell pressure and strong fundamentals | `date={"from": "2025-10-01T00:00:00Z", "to": "2025-10-06T23:59:59Z"}` | `filters={"buy_sell_pressure": {"min": 100000}, "open_interest": {"min": 500000}}` | Perps showing high buy/sell pressure and strong open interest |
| Discover perps favored by smart money | `date={"from": "2025-10-01T00:00:00Z", "to": "2025-10-06T23:59:59Z"}` | `only_smart_money=true` `filters={"smart_money_volume": {"min": 100000}}` | Perps with the highest smart money volume |

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | object | Yes | ISO 8601 date range |
| `pagination` | object | No | Page and per_page parameters |
| `filters` | object | No | Additional filters |
| `order_by` | array | No | Custom sort order |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| `token_symbol` | string | Filter by token symbol |
| `volume` | `{"min": number, "max": number}` | Filter by volume |
| `buy_sell_pressure` | `{"min": number, "max": number}` | Filter by buy/sell pressure |
| `open_interest` | `{"min": number, "max": number}` | Filter by open interest |
| `smart_money_volume` | `{"min": number, "max": number}` | Filter by smart money volume |

### Example Request

```http
POST /api/v1/perp-screener HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json

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

### Example Response

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

## 5. Perp PnL Leaderboard

**Endpoint:** `POST https://api.nansen.ai/api/v1/tgm/perp-pnl-leaderboard`

Rank traders by their profit/loss performance for a specific perpetual contract on Hyperliquid. Shows both realized profits (from completed trades) and unrealized profits (from current holdings).

### Key Features:

- Hyperliquid perpetual contracts only (no chain field needed)
- Realized and unrealized PnL tracking
- ROI calculations and trading patterns
- Position size and balance tracking

### Common Scenarios

| Usecase | Required Parameters | Optional Filters | Expected Output |
|---------|---------------------|------------------|-----------------|
| Filter for high-profit and high-balance addresses | `token_symbol="ETH"` `date={"from": "2025-10-14", "to": "2025-10-15"}` | `filters={"pnl_usd_realised": {"min": 100000}, "position_value_usd": {"min": 100000}}` | Only addresses with at least $100k realized PnL and $100k+ in position value |
| Surface only smart money traders for a specific contract | `token_symbol="SOL"` `date={"from": "2025-10-14", "to": "2025-10-15"}` | `filters={"trader_address_label": "Smart Money"}` | Leaderboard limited to Smart Money traders |

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token_symbol` | string | Yes | Perpetual contract symbol (e.g., BTC, ETH, SOL) |
| `date` | object | Yes | ISO 8601 date range |
| `pagination` | object | No | Page and per_page parameters |
| `filters` | object | No | Additional filters |
| `order_by` | array | No | Custom sort order |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| `pnl_usd_realised` | `{"min": number, "max": number}` | Filter by realized PnL |
| `position_value_usd` | `{"min": number, "max": number}` | Filter by position value |
| `trader_address_label` | string | Filter by trader label |

### Example Request

```http
POST /api/v1/tgm/perp-pnl-leaderboard HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json

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
      "direction": "DESC"
    }
  ]
}
```

### Example Response

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

---

## 6. Smart Money Perp Trades

**Endpoint:** `POST https://api.nansen.ai/api/v1/smart-money/perp-trades`

Access real-time perpetual trading activity from smart traders and funds on Hyperliquid. This endpoint provides granular transaction-level data showing exactly what sophisticated traders are trading on perpetual contracts.

### Key Features:

- Hyperliquid perpetual contracts only (no chain field needed)
- Real-time trading data from smart money wallets
- Detailed trade information including coin, amount, price, action, and type
- Smart money filtering capabilities
- Type filtering (Market/Limit)
- Only new positions filter to show only position opening trades (defaults to false - shows all trades)

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filters` | object | No | Additional filters |
| `only_new_positions` | boolean | No | When True, includes only 'Open' position actions (default: false) |
| `pagination` | object | No | Page and per_page parameters |
| `order_by` | array | No | Custom sort order |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| `action` | string | Filter by action (e.g., "Buy - Add Long") |
| `side` | string | Filter by side ("Long" or "Short") |
| `token_symbol` | string | Filter by token symbol |
| `type` | string | Filter by order type ("Limit" or "Market") |
| `value_usd` | `{"min": number, "max": number}` | Filter by trade value |

### Example Request

```http
POST /api/v1/smart-money/perp-trades HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json

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
      "direction": "DESC"
    }
  ]
}
```

### Example Response

```json
{
  "data": [
    {
      "trader_address_label": "Smart Money",
      "trader_address": "0x...",
      "token_symbol": "BTC",
      "side": "Long",
      "action": "Add",
      "token_amount": 1,
      "price_usd": 1,
      "value_usd": 1,
      "type": "Market",
      "block_timestamp": "2025-10-01T12:00:00Z",
      "transaction_hash": "0x..."
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

## 7. Token Perp Positions

**Endpoint:** `POST https://api.nansen.ai/api/v1/tgm/perp-positions`

Retrieve current perpetual positions for a specific token on Hyperliquid. Shows active positions with detailed metrics including entry price, mark price, leverage, PnL, and liquidation price.

### Key Features:

- Hyperliquid perpetual contracts only (no chain field needed)
- Real-time position tracking with live PnL calculations
- Leverage and margin information
- Smart money filtering capabilities
- Support for both Long and Short positions

### What it helps to answer:

1. What are the current perp positions for a specific token?
2. Which addresses have the largest positions by value?
3. What are the unrealized gains/losses on current positions?
4. What leverage levels are traders using?
5. Which smart money wallets are holding positions?

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token_symbol` | string | Yes | Token symbol (e.g., BTC) |
| `label_type` | string | No | Label type filter: `all_traders`, `smart_money`, `whale`, `public_figure` (default: `all_traders`) |
| `pagination` | object | No | Page and per_page parameters |
| `filters` | object | No | Additional filters |
| `order_by` | array | No | Custom sort order |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| `include_smart_money_labels` | array | Filter by smart money labels |
| `position_value_usd` | `{"min": number, "max": number}` | Filter by position value |
| `side` | array | Filter by side (["Long"] or ["Short"]) |
| `upnl_usd` | `{"min": number, "max": number}` | Filter by unrealized PnL |

### Example Request

```http
POST /api/v1/tgm/perp-positions HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json

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
      "field": "position_value_usd",
      "direction": "DESC"
    }
  ]
}
```

### Example Response

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

---

## 8. Token Perp Trades

**Endpoint:** `POST https://api.nansen.ai/api/v1/tgm/perp-trades`

Retrieve perpetual trade data for a specific token on Hyperliquid. Shows individual trades with detailed information including trader address, trade side (Long/Short), action type (Add/Reduce/Open/Close), order type (Market/Limit), and trade metrics.

### Key Features:

- Hyperliquid perpetual contracts only
- Smart money filtering capabilities
- Detailed trade breakdown with parsed action fields
- Support for both Long and Short position trading
- Market and Limit order types

### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token_symbol` | string | Yes | Token symbol to fetch trades for (e.g., "BTC", "ETH") |
| `date` | object | Yes | ISO 8601 date range |
| `pagination` | object | No | Page and per_page parameters |
| `filters` | object | No | Additional filters |
| `order_by` | array | No | Custom sort order |

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| `order_type` | array | Filter by order type (["MARKET"] or ["LIMIT"]) |
| `side` | array | Filter by side (["Long"] or ["Short"]) |
| `action` | array | Filter by action type |

### Example Request

```http
POST /api/v1/tgm/perp-trades HTTP/1.1
Host: api.nansen.ai
apiKey: YOUR_API_KEY
Content-Type: application/json

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
    "order_type": [
      "MARKET"
    ],
    "side": [
      "Long"
    ]
  },
  "order_by": [
    {
      "field": "block_timestamp",
      "direction": "DESC"
    }
  ]
}
```

### Example Response

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

---

## Error Responses

All endpoints return standard HTTP error codes:

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Content - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Pagination

All list endpoints support pagination with the following parameters:

```json
{
  "pagination": {
    "page": 1,
    "per_page": 10
  }
}
```

Response includes pagination metadata:

```json
{
  "pagination": {
    "page": 1,
    "per_page": 10,
    "is_last_page": true
  }
}
```

---

## Sorting

Most endpoints support custom sorting with the `order_by` parameter:

```json
{
  "order_by": [
    {
      "field": "position_value_usd",
      "direction": "DESC"
    }
  ]
}
```

Supported directions: `ASC`, `DESC`
