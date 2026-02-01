# Core Features & Capabilities

The Intelligent Zerodha Investment Agent is more than just a trading script; it is a full-featured investment management ecosystem.

## 🧠 AI-Driven Research
- **Cynical Risk Protocol**: The agent is programmed to prioritize safety over returns. It scans for governance issues, regulatory bans, and leadership instability.
- **Sentiment & Impact Scoring**: News is scored on a scale (Noise vs. Critical). Only high-impact, material news affects investment decisions.
- **Multimodal Reasoning**: Uses Gemini 2.0's large context window to correlate cross-sector trends (e.g., how a move in Utilities might affect your Industrial holdings).

## 📊 Dynamic Portfolio Portfolio
- **Trading Workspace**: A live, editable GUI to review AI suggestions.
- **Manual Overrides**: Humans have the final word. Adjust quantities or dismiss suggestions before execution.
- **Snapshot Persistence**: Once trades are queued, the UI captures a complete snapshot of the "Why" (LTP, Rationale, Signal) so you always know what you approved.

## 🛡️ Security & Enterprise Governance
- **Zero-Access Secrets**: No passwords or keys are stored in code or config files. Everything resides in Google Secret Manager.
- **Identity Pinning**: Only authorized Google User IDs can access the dashboard.
- **Hardened Cancellation**: Explicit controls to clear queued orders and reset to a clean draft state.

## 📈 Analytics & Insights
- **AI Logic Stream**: View the raw thinking process of the agent for setiap stock.
- **Executive Summaries**: AI-generated summaries of complex research runs to save you time.
- **Sector/Cap Mixed Distribution**: Real-time visualization of your portfolio's diversity.

## 🚀 Automation
- **Scheduled Nudges**: (Optional) Cloud Scheduler can trigger the agent to send you a Slack/Email notification when a rebalance is due.
- **Bi-Monthly Rebalancing**: Designed optimized for long-term compounding with minimal churn.
