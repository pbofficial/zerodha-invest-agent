# Configuration Guide

The agent's behavior is governed by two JSON files located in `src/config/`. For ease of use, you can copy the `*.example` files to get started.

## 1. `agent_config.json`
Controls the agent's mindset, financial budget, and high-level strategy.

| Field | Type | Description |
| :--- | :--- | :--- |
| `agent_settings.model_name` | string | The Vertex AI model used (recommended: `gemini-2.0-flash`). |
| `agent_settings.location` | string | GCP region for AI inference. |
| `agent_settings.risk_threshold` | integer | 1-10 scale. Higher means more "cynical" and less likely to trade. |
| `investment_goals.budget` | number | Total amount (₹) to allocate across all stocks in a single run. |
| `investment_goals.target_portfolio` | string | Comma-separated list of symbols the agent prioritizes for rebalancing. |
| `scoring_rules` | object | Weightage given to Noise (0), Context (5), and Critical (10) news events. |

## 2. `universe.json`
Defines the "Allowable Universe" of assets the agent is permitted to analyze.

### Asset Schema
```json
{
  "ticker": "RELIANCE",
  "type": "Core",
  "sector": "Energy",
  "cap_type": "Large",
  "target_amount": 50000,
  "target_weight": 0.20
}
```

| Field | Description |
| :--- | :--- |
| `ticker` | Trading symbol (without 'NSE:' prefix). |
| `type` | Classification: `Core`, `Growth`, `High Risk`, `ETF`, `REIT`. |
| `sector` | Industry category (used for diversification checks). |
| `cap_type` | `Large`, `Mid`, `Small`, or `Liquid`. |
| `target_amount` | The maximum flat ₹ value you want to hold in this stock. |
| `target_weight` | The maximum % of your total portfolio this stock should occupy. |

## Why JSON?
By separating the **Code** from the **Config**, you can update your portfolio targets or trading strategies without ever touching the Python logic. This follows the **Configuration as Code** philosophy.
