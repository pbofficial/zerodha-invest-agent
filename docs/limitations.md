# Operational Limitations & Known Hazards

While the Intelligent Zerodha Investment Agent is built with advanced AI and enterprise-grade guardrails, it is not "foolproof." Users must be aware of the following operational limitations and dependencies.

## 1. API Dependencies & Rate Limits 🌐
- **Kite Connect API**: The system is strictly dependent on Zerodha's Kite API. If Zerodha's servers are down or their API undergoes a breaking change, the agent will fail to fetch portfolios or place trades.
- **Rate Limiting**: Zerodha enforces rate limits on order placement and data fetching. While the agent spaces out its requests, high-frequency manual clicking on the dashboard could trigger temporary blocks.
- **Yahoo Finance**: The system uses `yfinance` for broad market data. This is a community-maintained library and is subject to data latency or occasional connectivity issues.

## 2. Token Management 🔑
- **Daily Expiry**: Zerodha's `ACCESS_TOKEN` typically expires every morning. You **must** generate a fresh session token through the Zerodha login portal and update your GCP Secret Manager before the agent can function for the day.
- **Manual Step**: Automating the login (handling 2FA/TOTP) is purposely avoided to maintain security. This means there is a daily manual maintenance step required.

## 3. Data Latency ⏱️
- **Not for Scalping**: The agent is designed for **Bi-Monthly Rebalancing**. Calculations are based on "Snapshot" prices, not tick-by-tick real-time data. 
- **Execution Slippage**: Since the user reviews the trade first, the price may have slightly changed by the time the order is actually pushed to the exchange.

## 4. Financial & Logical Risks 📉
- **Black Swan Events**: AI news analysis is limited to what is publicly available and searchable. It cannot predict sudden, unannounced global events or "flash crashes."
- **Portfolio Specifics**: The agent relies on the `universe.json` you provide. If you provide symbols with very low liquidity, your trade execution may fail or suffer from high impact costs.

## 5. Human-in-the-Loop Burden 👤
- **Confirmation Requirement**: If you do not log in to the dashboard to "Confirm" a draft, the system will never place a trade. The "Order Pusher" scheduler only processes orders you have already scrutinized and queued.

## 6. Infrastructure Costs
- **Compute Costs**: Running Cloud Run, Cloud Functions, and Vertex AI (Gemini) incurs costs on your GCP bill. While optimized for "Pay-as-you-go," frequent runs or high-usage models can increase monthly overhead.

---
**Summary**: This tool is an **Analytics Assistant**, not a "Money Printing Machine." Use it to augment your research, but never rely on it as a single source of truth for high-stakes decisions without independent verification.
