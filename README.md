# Intelligent Zerodha Investment Agent

> [!WARNING]
> **Financial Disclaimer**: This software is **not financial advice**. It is an experimental tool provided for educational and research purposes only. The authors and contributors are not responsible for any financial losses incurred through the use of this system. **Use at your own risk.** Update and audit the code to align with your personal risk profile.

An AI-powered agentic system built on Google Cloud Platform for automated, bi-monthly stock allocation in the Indian markets (Zerodha).

## 🚀 Key Features
- **Brain**: Vertex AI (Gemini) for news analysis and reasoning.
- **Hands**: Python-based automation for precise math and Kite Connect API calls.
- **Security**: Hardened authentication via GCP Secret Manager.
- **Dashboard**: Real-time Streamlit interface for portfolio analytics and trade execution.

## 📖 Documentation Portal
For a deep dive into how this system works, please refer to the following guides:

- **[System Architecture](docs/architecture.md)**: Deep dive into the Brain (AI) vs. Hands (Python) logic.
- **[Lifecycle & User Flow](docs/lifecycle.md)**: Understanding automation triggers and the "Human-in-the-Loop" process.
- **[AI Governance & Guardrails](docs/ai_governance.md)**: How we prevent hallucinations and ensure clinical mathematical precision.
- **[Transparency & Limitations](docs/limitations.md)**: Addressing API dependencies, token expiry, and operational risks.
- **[Core Features](docs/features.md)**: Detailed list of analysis and dashboard capabilities.
- **[Configuration Guide](docs/configuration.md)**: How to customize your portfolio universe and agent mindset.

## 🤖 Is it Agentic?
Yes. Unlike a standard script, this system is **Agentic** because:
1. **Autonomous Reasoning**: The AI doesn't just follow a list; it investigates news, correlates sentiment, and decides *if* a trade is worth the risk.
2. **Tool Use**: The "Brain" (Gemini) calls specific "Hands" (Python functions) to fetch real-time data, ensuring it never hallucinates a stock price.
3. **Internal Feedback Loop**: The agent scoring system filters its own research, dismissing "Noise" before it ever reaches your dashboard.

## 🎯 Why This Exists?
Most trading bots are "Fast and Loose." This agent is **Slow and Cynical**. 
- It treats bad news as a "Sell" signal by default.
- It requires human confirmation before a single rupee is spent.
- It leverages **Anti-Hallucination Guardrails** to separate AI logic from mathematical execution.

## 🛠️ Tech Stack
- **AI**: Gemini 2.0 Flash (Vertex AI)
- **Infrastructure**: Terraform, Cloud Functions, Cloud Run, Firestore
- **Backend**: Python 3.12, Pandas, yfinance
- **Auth**: Kite Connect API

## 📋 Getting Started

### 1. Prerequisites
- Google Cloud Project with Billing enabled.
- Zerodha (Kite Connect) API credentials.
- Terraform installed locally.

### 2. Configuration
The agent relies on two core JSON configuration files in `src/config/`:
- `agent_config.json`: Defines the agent mindset, budget, and target portfolio.
- `universe.json`: Defines the universe of allowable stocks with sector and cap classifications.

*See `*.example` files for templates.*

### 3. Setup Secrets
The following secrets must be created in Google Secret Manager:
- `KITE_API_KEY`
- `KITE_API_SECRET`
- `KITE_ACCESS_TOKEN`
- `GMAIL_USER` (Sender email for notifications)
- `GMAIL_APP_PASSWORD` (App password for Gmail SMTP)
- `RECIPIENT_EMAIL` (Target email for trade reports)
- `ALLOWED_USER_ID` (For dashboard authentication)

### 4. Deployment
Run the deployment script for your environment:

**Windows (PowerShell):**
```powershell
.\deploy.ps1 -ProjectId YOUR_PROJECT_ID -RecipientEmail YOUR_EMAIL
```

**Linux / macOS (Bash):**
```bash
chmod +x deploy.sh
./deploy.sh YOUR_PROJECT_ID YOUR_EMAIL
```

## ⚖️ Governance
The system uses a **Human-in-the-loop** model. The AI suggests trades, but execution requires manual approval via the Streamlit Dashboard.

## 🚀 Future Roadmap & Recommendations
To improve the robustness and utility of this agent, the following enhancements are recommended:
1. **Dynamic Risk Weighting**: Integrate a "Fear & Greed" index to automatically adjust the global `risk_threshold`.
2. **Multi-Broker Support**: Abstract the trade execution layer to support brokers beyond Zerodha (e.g., Upstox, Groww).
3. **Advanced Technical Indicators**: Allow the Agent to fetch RSI/MACD data as additional "Hands" for technical correlation.
4. **Model Context Protocol (MCP) Integration**: Transition the "Tool" layer to MCP to allow for plug-and-play research and execution modules.
5. **Historical Backtesting**: Create a simulation mode to test AI logic against past market crashes.
6. **Enhanced LLM Observability**: Integrate LangSmith or Vertex AI evaluation to track reasoning accuracy over time.

---
*Disclaimer: This is an experimental tool. Trading stocks involves high risk.*