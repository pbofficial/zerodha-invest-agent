# Zerodha Investment Agent: MCP Architecture & Manual Setup

## 1. Architecture Overview

### Why MCP?
We use the **Model Context Protocol (MCP)** to decouple the AI Reasoning Layer (Vertex AI) from the Execution Layer (Cloud Functions).
- **Standardization**: All tools share a common schema.
- **Security**: Apigee acts as the "Gateway," enforcing API keys and traffic inspection before it hits our internal Cloud Functions.
- **Portability**: The AI doesn't need to know *where* a tool is hosted, only *how* to call it via MCP.

### Data Flow
1. **User Query** -> Vertex AI (Gemini)
2. **Tool Call** -> "I need to call `get_market_data`"
3. **MCP Adapter** (`src/agent/mcp_advisor.py`) -> Calls Apigee Proxy (`/mcp/v1/get_market_data`)
4. **Apigee Proxy** -> RouteRule -> Specific Cloud Function (e.g., `get-portfolio`)
5. **Cloud Function** -> Zerodha/Yahoo API -> Response

---

## 2. "Smart Bundling" Deployment
To keep our source code **generic** (no hardcoded Project IDs) while ensuring a working app, we use a **Smart Bundling** technique in `deploy.ps1`.

### How it works:
1. **Dynamic Discovery**: The script (`deploy.ps1` calls `bundle_apigee.ps1`) fetches your *actual* Cloud Run URLs.
2. **Injection**: It copies the Apigee proxy files to a temp folder and **injects** these URLs into the Target XMLs.
3. **Bundling**: It zips this *modified* folder and deploys it to your Apigee Org (Environment configurable via `-ApigeeEnv`).

**Result**: You get a custom-tailored Apigee proxy automatically during the main deployment, targeting your specific environment (eval, prod, etc.).

---

## 3. Manual Setup Guide (If Automated Scripts Fail)

If `deploy.ps1` hits a snag, you can set up the core components manually:

### Step 1: Create Apigee Environment
1. Go to **Apigee Console** in GCP.
2. Create an Environment named `eval` (or whatever you prefer).
3. Attach it to a **hostname** (e.g., `investment-agent.example.com`).

### Step 2: Deploy the Proxy
1. **Zip** the `apigee/proxies/investment-agent-mcp/apiproxy` folder.
2. **Upload** this Zip to Apigee -> **Proxies** -> **Create New** -> **Upload Bundle**.
3. **Important**: You MUST manually update the `<URL>` in the Target Endpoints (`targets/*.xml`) to match your Cloud Run URLs if you skipped the smart script.

### Step 3: Create Product & App
1. **Products**: Create a Product named `InvestmentAgentProduct`. Add the `investment-agent-mcp` proxy to it.
2. **Apps**: Create a Developer App. Select `InvestmentAgentProduct`.
3. **Credentials**: Copy the **Consumer Key**. This is your `APIGEE_API_KEY`.
4. Add this key to **Secret Manager** as `APIGEE_API_KEY`.

### Step 4: API Hub Registration (Optional but Recommended)
1. Go to **API Hub**.
2. Register your API as `investment-agent-mcp`.
3. Upload the OpenAPI Spec (if available) or link to the Apigee Proxy.

---

## 4. Fallback Mechanism
If Apigee goes down or is unreachable, the Agent (`mcp_advisor.py`) has a failsafe:
- It detects the connection error.
- It logs a warning: `⚠️ MCP Endpoint Unreachable`.
- behavior depends on strictness: It may either fail safely (refusing to trade) or fall back to a limited "Safe Mode" if configured (currently set to fail safe for security).
