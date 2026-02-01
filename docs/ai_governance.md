# AI Governance & Anti-Hallucination Guardrails

One of the greatest risks in LLM-based systems is **hallucination**—where the AI confidently presents false data. In a financial context, this is unacceptable. This system uses a multi-layered guardrail architecture to ensure mathematical and clinical precision.

## 1. The "Hands vs. Brain" Protocol 🛡️
The system implements a strict separation of concerns:
- **The Brain (Vertex AI)**: Responsible for *reasoning*, *sentiment analysis*, and *recommendation logic*. It is never allowed to calculate financial results or fetch data directly.
- **The Hands (Python Tools)**: Responsible for *deterministic calculations*, *API calls*, and *real-time data fetching*. 

**How it prevents hallucination**: If the AI wants to know the price of RELIANCE, it cannot "guess." It must call the `market_data` tool. The result returned to the AI is the single source of truth from Zerodha/Kite.

## 2. Structured Output Enforcement
The agent is constrained to output its analysis in a strict JSON schema. If the AI deviates from this schema (e.g., trying to write a poetic explanation instead of a trade list), the system's validation layer will catch it before any data is persisted.

## 3. Human Gatekeeping (Override Power) 👤
Even if the AI provides a perfect analysis, it has **zero execution authority**.
- **Review Requirement**: Every AI-suggested quantity is displayed in the Trading Workspace.
- **Full Overrides**: You can manually change the "Buy Qty" to `0` to dismiss a suggestion, or increase/decrease it based on your intuition. 
- **Snapshot Integrity**: Once you click "Confirm," the system saves a snapshot of the *exact* values you reviewed, preventing any "slippage" between review and execution.

## 4. News Sanitization & Context Window
The Agent doesn't just "search the web." It uses a guided search process to fetch specific news headers and summaries, which are then passed into the prompt as verified context strings. This prevents the model from relying on its internal training data (which may be outdated) for current market events.

## 5. Mathematical Resilience
Trade quantities are calculated using Python's `math` and `pandas` libraries, not LLM arithmetic. The budget allocation logic is deterministic:
```python
# Conceptual logic performed by "Hands", NOT the AI:
buy_qty = floor(remaining_budget / live_price)
```
This ensures that your budget limits are strictly enforced by code, not by AI "vibes."
