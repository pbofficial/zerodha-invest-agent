# Configuration Guide

The agent's behavior is governed by dynamic configuration stored in **Google Cloud Firestore**. While local JSON files in `src/config/` serve as templates and fallbacks, your "Source of Truth" lives in the cloud for maximum security and ease of management.

## 0. Cloud-First Management 🛰️
Once deployed, you can manage your settings directly via the **Dashboard -> ⚙️ Config** tab. Changes made there are instantly persisted to Firestore and picked up by the Agent's next run.

---

## 1. `agent_config.json` (Template)
Controls the agent's mindset, financial budget, and high-level strategy.

| Field | Type | Description |
| :--- | :--- | :--- |
| `agent_settings.model_name` | string | The Vertex AI model used (recommended: `gemini-2.0-flash`). |
| `agent_settings.location` | string | GCP region for AI inference (e.g., `us-east4`). |
| `agent_settings.risk_threshold` | integer | 1-10 scale. Higher means more "cynical" and less likely to trade. |
| `investment_goals.budget` | number | Total amount (₹) to allocate across all stocks in a single run. |
| `investment_goals.target_portfolio` | string | Comma-separated list of symbols the agent prioritizes for rebalancing. |
| `scoring_rules` | object | Weightage given to Noise (0), Context (5), and Critical (10) news events. |

---

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

---

## 3. Secret Reference (Secret Manager)
While the files above control the *strategy*, the *security* is handled via GCP Secret Manager.

| Secret Name | Description |
| :--- | :--- |
| `KITE_API_KEY` | Your Zerodha API Key. |
| `KITE_API_SECRET` | Your Zerodha API Secret. |
| `KITE_ACCESS_TOKEN` | Your daily Zerodha Access Token. |
| `GMAIL_USER` | The email address used to send market reports (must be a @gmail.com or Workspace account). |
| `GMAIL_APP_PASSWORD` | 16-character Google App Password. [Generate here](https://support.google.com/accounts/answer/185833). **Crucial**: Standard passwords will not work. |
| `ALLOWED_USER_ID` | **Your Zerodha User ID** (e.g., `AB1234`). This is required for session validation and ensures only your account can use the pinned tokens. |
| `RECIPIENT_EMAIL` | The target email address for trade reports and rebalance alerts. |

---

## Why JSON?
By separating the **Code** from the **Config**, you can update your portfolio targets or trading strategies without ever touching the Python logic. This follows the **Configuration as Code** philosophy.
