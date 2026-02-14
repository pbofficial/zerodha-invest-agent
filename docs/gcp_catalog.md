# GCP Component Catalog

This document provides a comprehensive list of all Google Cloud Platform services used in the **Zerodha Invest Agent** project. Use this as a reference for discovery, troubleshooting, and console access.

---

## 🏗️ Core Infrastructure

### 1. Apigee (MCP Gateway)
- **Role**: The "Gatekeeper" and "Router" for all AI tool calls.
- **Key Resources**:
    - **Proxy**: `investment-agent-mcp` (Handles MCP `list_tools` and `call_tool`).
    - **Environment**: Typically `eval` or `prod`.
    - **Environment Group**: Where your **Hostname** is defined.
    - **Products**: `InvestmentAgentProduct` (Bundles the proxy for access).
    - **Developer App**: Provides the `Consumer Key` used as `APIGEE_API_KEY`.
- **Discovery**: [Apigee Console](https://console.cloud.google.com/apigee)

### 2. API Hub (Registry)
- **Role**: Universal directory for tool discovery and documentation.
- **Key Resources**:
    - **APIs**: `get-market-snapshot`, `check-financial-health`, `calculate-allocations`, `get-market-news`.
    - **MCP Styling**: APIs with the `system-api-style: mcp-api` attribute display the specialized MCP interface.
- **Discovery**: [API Hub Dashboard](https://console.cloud.google.com/apihub)

---

## 🧠 Reasoning & Execution

### 3. Vertex AI (The Brain)
- **Role**: Generative AI reasoning via Gemini.
- **Model**: `gemini-2.0-flash` (Recommended for speed and math precision).
- **Location**: Defined in `terraform/variables.tf` (default: `us-east4`).
- **Discovery**: [Vertex AI Console](https://console.cloud.google.com/vertex-ai)

### 4. Cloud Run (The Dashboard)
- **Role**: Hosts the Streamlit-based command center.
- **Service Name**: `zerodha-agent-dashboard`.
- **Discovery**: [Cloud Run Services](https://console.cloud.google.com/run)

### 5. Cloud Functions (The Hands)
- **Role**: Deterministic Python code that interacts with Zerodha and other APIs.
- **Functions**:
    - `get-portfolio`: NSE holdings and LTP.
    - `calculate-allocations`: The math engine.
    - `check-financial-health`: Cynical profit audit.
    - `get-market-news`: Focused risk search.
- **Discovery**: [Cloud Functions Console](https://console.cloud.google.com/functions)

---

## 🔐 State & Security

### 6. Secret Manager
- **Role**: Vault for all sensitive keys.
- **Required Secrets**: `KITE_API_KEY`, `KITE_API_SECRET`, `GMAIL_APP_PASSWORD`, `APIGEE_API_KEY`.
- **Discovery**: [Secret Manager](https://console.cloud.google.com/security/secret-manager)

### 7. Firestore (State)
- **Role**: NoSQL database for portfolio history and audit logs.
- **Collections**: `config`, `research_reports`, `orders`.
- **Discovery**: [Firestore Studio](https://console.cloud.google.com/firestore)

### 8. Cloud Scheduler (Automation)
- **Role**: Triggers the morning execution bot.
- **Job Name**: `morning-execution-bot`.
- **Schedule**: `15 9 * * 1-5` (9:15 AM IST, Mon-Fri).
- **Discovery**: [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler)
