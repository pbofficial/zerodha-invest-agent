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

## 🤖 Standard Workflow
The platform is designed for a **bi-monthly** rebalancing cycle:

1.  **⚙️ Configure**: Use the **Config** tab in the Dashboard to set your budget, stock universe, and AI risk profile. These are saved to **GCP Firestore** and act as the "Source of Truth."
2.  **🤖 Run Analysis**: Click "Run Analysis" in the **Workspace** tab. The AI will research news and financials for your universe and propose a specific buy/sell list.
3.  **🖥️ Review & Submit**: Review the AI rationale for each stock in the interactive table. Edit quantities if needed, then click "Submit for Approval."
4.  **🚀 Automated Execution**: Once approved, the **Morning Execution Bot** (Cloud Scheduler) will automatically place the orders at market open (9:15 AM IST).

## 📋 Getting Started

### 1. Prerequisites
- Google Cloud Project with Billing enabled.
- Zerodha (Kite Connect) API credentials.
- Terraform installed locally.

### 2. Setup Secrets
The system uses **GCP Secret Manager** for all sensitive credentials. You MUST create these secrets in your project before deploying:

| Secret Name | Description | Where to find it? |
| :--- | :--- | :--- |
| `KITE_API_KEY` | Your Zerodha App API Key. | [Kite Connect Dashboard](https://kite.trade/apps) |
| `KITE_API_SECRET` | Your Zerodha App API Secret. | [Kite Connect Dashboard](https://kite.trade/apps) |
| `KITE_ACCESS_TOKEN` | The 32-char session token. | Generated daily via manual login (or automated script). |
| `ALLOWED_USER_ID` | Your Zerodha User ID (e.g. `AB1234`). | Locks the Dashboard to your specific session. |
| `GMAIL_USER` | The Gmail address used to send reports. | Your personal Gmail address. |
| `GMAIL_APP_PASSWORD` | A 16-character 'App Password'. | [Google Account > Security > App Passwords](https://myaccount.google.com/apppasswords) |
| `RECIPIENT_EMAIL` | Where alerts and plans are sent. | Any email address where you want to receive nudge reports. |

> [!TIP]
> **Gmail App Password**: Standard Gmail passwords will NOT work. You must enable 2FA and generate a dedicated App Password for the "Mail" app on "Other (Custom name)".

### 3. Deployment
Run the unified deployment script. This will provision your Cloud Functions, Firestore database, and the Streamlit Dashboard.
```powershell
.\deploy.ps1 -ProjectId "your-gcp-project-id" -RecipientEmail "your@email.com"
```

### 4. Initial Load
After deployment, go to the **Config** tab in your Streamlit Dashboard. Upload or enter your stock universe and budget. The agent will prefer these cloud values over local files.

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