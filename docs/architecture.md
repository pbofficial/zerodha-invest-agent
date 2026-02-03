# System Architecture

The Intelligent Zerodha Investment Agent is designed with a strict **Separation of Concerns**, ensuring that AI reasoning never interferes with deterministic execution logic.

## High-Level Architecture

```mermaid
graph TD
    User((User)) --> Dashboard[Streamlit Dashboard]
    
    subgraph GCP ["Google Cloud Platform"]
        Dashboard --> CloudRun[Cloud Run]
        CloudRun --> Firestore[(Firestore State)]
        CloudRun --> Secrets[Secret Manager]
        
        subgraph AgentBrain ["The Brain"]
            CloudRun --> VertexAI[Gemini 2.0 Flash]
        end
        
        subgraph AgentHands ["The Hands"]
            VertexAI --> Tools[Python Tool Functions]
            Tools --> KiteAPI[Kite Connect API]
            Tools --> YFinance[Yahoo Finance]
            Tools --> News[Market News API]
        end
    end
    
    CloudRun --> AgentBrain
```

## Core Components

### 1. The Dashboard (UI/UX)
- **Technology**: Streamlit / Python.
- **Role**: Serves as the Command Center. Provides real-time analytics, risk profiling, and the **Human-in-the-Loop** approval interface.
- **Security**: Hardened via `ALLOWED_USER_ID` pinning and Cloud Run IAM.

### 2. The Agent Reasoning (Brain)
- **Technology**: Vertex AI (Gemini 2.0 Flash).
- **Role**: High-speed news digestion and risk modeling. It applies the "Cynical Risk Manager" protocol to every ticker in the universe.
- **Logic Sync**: Every run generates a full JSON research report for the 30-stock universe, which is persisted to Firestore.

### 3. The Tool Layer (Hands)
- **Role**: Deterministic execution. The AI performs the "Thinking," but these functions perform the "Doing" (Fetching prices, calculating exact order quantities, placing trades).
- **Integrations**:
    - **Kite Connect**: Order placement and portfolio fetching.
    - **yfinance**: Real-time pricing and historical data.
    - **DDG Search**: Decentralized news correlation.

### 4. State Management
- **Firestore**: Tracks the "Pending Orders" lifecycle (`DRAFT` -> `QUEUED` -> `EXECUTED`).
- **Secret Manager**: Securely stores API keys, tokens, and PII (emails).

## Data Flow: The Analysis Loop
1. User clicks **"Run Agent Analysis"**.
2. Dashboard triggers the Agent Logic Stream.
3. Agent fetches news for all 30 tickers in parallel.
4. Agent applies risk scoring based on Governance/Macro news.
5. Agent filters for financial health.
6. Agent calculates suggested quantities based on the global budget.
7. Agent saves a comprehensive Research Report to Firestore.
8. Dashboard refreshes to show refined AI Signals and Insights.

## The Paradigm Shift: From API Management to AI Management

As of Phase 2, this architecture evolves from traditional REST integration to **AI Management via APIs**. 

### 1. Model Context Protocol (MCP) as the Abstraction Layer
By using Apigee as an **MCP Gateway**, we decouple the "Brain" from the specific "Hands". 
- **The LLM** sees a stable set of capabilities (Tools).
- **Apigee** manages the lifecycle, discovery (via API Hub), and governance of these tools.
- **The Broker (Zerodha)** is abstracted away. Switching brokers in the future requires zero changes to the AI's reasoning logic.

### 2. Generative AI Policies (LLM Snaps)
We transition from basic rate limiting to **AI Governance**:
- **Prompt Sanitization**: Using Model Armor to prevent adversarial prompts.
- **Semantic Caching**: Reducing latency and cost by caching common financial queries.
- **Token Quotas**: managing "AI Spend" at the gateway level rather than inside the application code.

> [!NOTE]
> This transition marks the move from "building an app with AI" to "building an autonomous AI-driven enterprise service."
