
import os
import sys
import logging
import json
import traceback
import vertexai
from google.cloud import firestore
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration


# Add src to python path to import our local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

# Import Tool Implementations
from src.functions.market_data.main import get_market_snapshot
from src.functions.news.main import get_market_news
from src.functions.fundamentals.main import check_financial_health
from src.functions.allocation.main import calculate_orders
from src.utils.llm_helpers import extract_json_from_text
from src.utils.config_loader import config as cloud_config

def main(request=None):
    """Entry point for Cloud Function."""
    from io import StringIO
    import sys as sys_orig
    old_stdout = sys_orig.stdout
    sys_orig.stdout = result = StringIO()
    try:
        run_agent(auto_execute=True)
    except Exception as e:
        logger.error(f"Top-level execution error: {e}")
        traceback.print_exc(file=sys_orig.stdout)
    finally:
        sys_orig.stdout = old_stdout
    return result.getvalue()

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("InvestmentAgent")

# Defaults for import safety
AGENT_CONFIG = {}
UNIVERSE_CONFIG = {"assets": []}
SETTINGS = {}
GOALS = {}
SYSTEM_INSTRUCTION = ""
TARGET_PORTFOLIO_STR = ""

def load_universe_config():
    """Unified configuration loading via Cloud Config Loader."""
    global AGENT_CONFIG, UNIVERSE_CONFIG, SETTINGS, GOALS, SCORING, ASSETS
    
    # Fetch from Unified Cloud Loader
    AGENT_CONFIG = cloud_config.get_agent_settings()
    UNIVERSE_CONFIG = cloud_config.get_universe()

    SETTINGS = AGENT_CONFIG.get("agent_settings", {})
    GOALS = AGENT_CONFIG.get("investment_goals", {})
    SCORING = AGENT_CONFIG.get("scoring_rules", {})
    ASSETS = UNIVERSE_CONFIG.get("assets", [])
    
    logger.info(f"📍 Configuration Synchronized. Universe: {len(ASSETS)} tickers | Budget: {GOALS.get('budget')}")

def get_system_instruction(assets, settings, scoring):
    """Generates the system prompt dynamically based on the current universe."""
    
    # Prepare Universe String
    target_strings = []
    universe_tickers = []
    
    for a in assets:
        ticker = a.get("ticker")
        weight = a.get("target_weight", 0) * 100
        target_strings.append(f"{ticker} ({weight:.1f}%)")
        universe_tickers.append(ticker)
        
    universe_list_str = ", ".join(universe_tickers)
    
    # Construct System Prompt
    risk_threshold = settings.get("risk_threshold", 8)
    score_noise = scoring.get("noise", 0)
    score_context = scoring.get("context", 5)
    score_critical = scoring.get("critical", 10)

    instruction = f"""
You are a cynical Risk Manager for the Indian Market.
Your goal is to rebalance the portfolio bi-monthly, but safety is your primary directive.

When you receive news headlines, you must evaluate them for Material Financial Impact.

--- NEWS RELEVANCE PROTOCOL ---
Scoring Rules:
Score {score_noise} (Noise): Product launches, marketing campaigns, minor price moves, random blogs. -> IGNORE.
Score {score_context} (Context): Sector trends, competitor moves. -> NOTE ONLY.
Score {score_critical} (Critical): Governance issues, raids, CFO/CEO exits, earnings misses >20%, regulatory bans. -> ACTIONABLE.

Strict Rule: If the 'Governance Risk' score is below {risk_threshold}/10, assume the stock is SAFE. Do not hallucinate risks based on minor news.
-------------------------------

--- UNIVERSE ---
These are the ONLY stocks you are allowed to check and invest in:
{universe_list_str}
----------------

Process:
1. **MANDATORY FIRST STEP**: Call `get_market_snapshot(tickers=['ALL'])` to get the current portfolio and market prices for the ENTIRE universe.
2. Fetch News (get_market_news) for **ALL** tickers in the universe (pass the full list in one batch) to check for governance risks.
3. Apply the News Relevance Protocol. Calculate risk scores for each stock. 
   - NOTE: Tickers like 'EMBASSY-RR' are valid and mapped correctly; do not skip them.
4. Explain your thought process for **EVERY SINGLE TICKER** in the universe, even if briefly. Do not omit any from your analysis.
5. Filter out any stocks with a Risk Score >= {risk_threshold}.
6. Check Financial Health (check_financial_health) for **ALL** remaining candidates in one batch (pass list of tickers). Exclude any with 'WARNING' status.
7. Calculate Allocations (calculate_allocations) using the safe list and your budget. 
   - CRITICAL: The budget provided is the **TOTAL AGGREGATE** for the entire run. It must be distributed across all tickers. It is NOT a per-ticker limit.
9. Finalize the list. If a stock is missing from the proposal, clearly state WHY in your thoughts (e.g., 'Target Met', 'High Risk', or 'Exceeded Global Budget').

--- FINAL OUTPUT FORMAT ---
You must output a JSON list of trade recommendations for **EVERY SINGLE TICKER** in the universe (30 total entries).
[
  {{
    "ticker": "Symbol",
    "signal": "STRONG_BUY" | "BUY" | "ACCUMULATE" | "HOLD" | "SELL",
    "quantity": 5,
    "reason": "DETAILED EXPLANATION of news impact, fundamentals, and risk scores. Explain YOUR logic."
  }}
]
- If no action is needed, set signal to 'HOLD' and quantity to 0. 
- Do not wrap in markdown.
---------------------------

Chain of Thought:
Before calling tools and making final decisions, you MUST explain your thinking as plain text (e.g., 'Analyzing News for XYZ...'). 
In the final response, your JSON 'reason' field must be transparent and verbose enough for a human to trust.
"""
    return instruction, ", ".join(target_strings)

# --- 2. Tool Wrapping (Vertex AI) ---

get_market_snapshot_func = FunctionDeclaration(
    name="get_market_snapshot",
    description="Fetches current market snapshot (LTP and Holdings) for a list of tickers.",
    parameters={
        "type": "object",
        "properties": {
            "tickers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ticker symbols (e.g. ['NSE:RELIANCE'])"
            }
        },
        "required": ["tickers"]
    },
)

get_market_news_func = FunctionDeclaration(
    name="get_market_news",
    description="Fetches recent news headlines for tickers to check for governance risks or scandals.",
    parameters={
        "type": "object",
        "properties": {
            "tickers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of ticker symbols."
            }
        },
        "required": ["tickers"]
    },
)

calculate_allocations_func = FunctionDeclaration(
    name="calculate_allocations",
    description="Calculates the optimal stock allocations (orders) to rebalance the portfolio based on a TOTAL global budget.",
    parameters={
        "type": "object",
        "properties": {
            "budget": {
                "type": "number",
                "description": "The TOTAL amount of capital (INR) to distribute across the ENTIRE portfolio for this run."
            },
            "portfolio": {
                 "type": "array",
                 "items": {"type": "object"},
                 "description": "Current portfolio holdings list."
            },
             "prices": {
                 "type": "object",
                 "description": "Dictionary of current asset prices."
            },
             "targets": {
                 "type": "object",
                 "description": "Target allocation percentages for each asset."
            },
            "target_amounts": {
                 "type": "object",
                 "description": "Optional absolute target amounts (cost basis) for each ticker."
            }
        },
        "required": ["budget", "portfolio", "prices", "targets"]
    },
)


check_financial_health_func = FunctionDeclaration(
    name="check_financial_health",
    description="Checks the financial health of a stock (profit trends).",
    parameters={
        "type": "object",
        "properties": {
            "tickers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of NSE Ticker Symbols (e.g. ['HDFCBANK', 'RELIANCE'])"
            }
        },
        "required": ["tickers"]
    },
)

# Bundle functions into a Tool
invest_tool = Tool(
    function_declarations=[
        get_market_snapshot_func,
        get_market_news_func,
        check_financial_health_func,
        calculate_allocations_func
    ],
)

# --- 4. The Execution Flow ---

def save_draft_proposal(orders: list, audit_trail: str, merge: bool = False, full_analysis: list = None):
    """
    Saves the proposed orders as a DRAFT.
    - 'orders': Actionable trades (Qty > 0).
    - 'full_analysis': Complete list of all tickers analyzed (for Dashboard visibility).
    - 'ui_snapshot': NEVER deleted by Agent. Dashboard manages it.
    """
    from src.utils.llm_helpers import normalize_ticker
    import math

    logger.info(f"DEBUG: Saving draft. Orders={len(orders)}. Full Analysis={len(full_analysis) if full_analysis else 0}")
    project = os.environ.get("PROJECT_ID", "UNKNOWN")
    
    # Sanitization Helper
    def sanitize(item_list):
        clean_list = []
        for o in item_list:
            clean_o = {}
            for k, v in o.items():
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    clean_o[k] = 0.0
                else:
                    clean_o[k] = v
            clean_list.append(clean_o)
        return clean_list

    sanitized_orders = sanitize(orders)
    sanitized_analysis = sanitize(full_analysis) if full_analysis else []

    try:
        db = firestore.Client(project=project)
        pending_ref = db.collection("pending_orders").document("latest")
        
        final_orders = sanitized_orders
        final_analysis = sanitized_analysis
        final_audit = audit_trail
        
        # Merge Logic (Preserved for specific tickers)
        if merge:
            doc = pending_ref.get()
            if doc.exists:
                data = doc.to_dict()
                if data.get("status") in ["DRAFT", "NONE"]:
                    # Merge Orders
                    existing_orders = data.get("orders", [])
                    existing_map = {normalize_ticker(o["ticker"]): o for o in existing_orders if "ticker" in o}
                    for new_o in sanitized_orders:
                        existing_map[normalize_ticker(new_o["ticker"])] = new_o
                    final_orders = list(existing_map.values())
                    
                    # Merge Analysis (Critical for UI consistency)
                    existing_analysis = data.get("full_analysis", [])
                    analysis_map = {normalize_ticker(o["ticker"]): o for o in existing_analysis if "ticker" in o}
                    for new_a in sanitized_analysis:
                        analysis_map[normalize_ticker(new_a["ticker"])] = new_a
                    final_analysis = list(analysis_map.values())
                    
                    final_audit = data.get("audit_trail", "") + "\n\n--- PARTIAL UPDATE ---\n" + audit_trail
        
        update_data = {
            "orders": final_orders,          # Only Qty > 0 (Execution Queue)
            "full_analysis": final_analysis, # ALL Tickers (UI Visibility)
            "status": "DRAFT",
            "created_at": firestore.SERVER_TIMESTAMP,
            "audit_trail": final_audit,
            "rebalance_id": os.environ.get("DEPLOY_ID", "AUTO_RUN")
        }
        
        # CRITICAL: Do NOT delete ui_snapshot. Dashboard manages it.
        # update_data["ui_snapshot"] = firestore.DELETE_FIELD 
        
        pending_ref.update(update_data)
        return "DRAFT_SAVED"
    except Exception as e:
        logger.error(f"Failed to save draft: {e}")
        return "ERROR"

def run_agent(auto_execute=False, budget_override=None, specific_tickers=None, skip_notify=False):
    # Initialize Configuration (Lazy Load)
    load_universe_config()


    # Initialize Vertex AI
    # Use global SETTINGS and GOALS loaded from config
    
    # Initialize Vertex AI
    # Use global SETTINGS and GOALS loaded from config
    
    from src.utils.project import get_project_id, get_location, get_model_name
    project_id = get_project_id()
    location = get_location()
    model_name = get_model_name()
    
    logger.info(f"🚀 Initializing Vertex AI: Project={project_id} | Location={location} | Model={model_name}")
    
    if not project_id:
        logger.warning("⚠️ PROJECT_ID resolution failed. Vertex AI init might fail or use default.")
    
    vertexai.init(project=project_id, location=location)
    
    # --- DYNAMIC PROMPT CONSTRUCTION ---
    # Ensure ASSETS are fresh from the loaded config
    current_assets = UNIVERSE_CONFIG.get("assets", [])
    
    if specific_tickers:
        logger.info(f"Refining analysis for tickers: {specific_tickers}")
        # Normalize to upper case
        specific_tickers = [t.strip().upper() for t in specific_tickers]
        # Filter Assets
        current_assets = [a for a in current_assets if a['ticker'] in specific_tickers]

    # Generate System Instruction for THIS run
    system_instruction, target_portfolio_str = get_system_instruction(current_assets, SETTINGS, SCORING)
    
    # Override target string if present in config for more natural prompt
    if GOALS.get("target_portfolio"):
        target_portfolio_str = GOALS.get("target_portfolio")

    # --- TOOL & FUNCTION SETUP ---
    use_apigee = os.environ.get("USE_APIGEE_MCP", "false").lower() == "true"
    mcp_advisor = None
    
    if use_apigee:
        logger.info("🚀 Using Apigee MCP for Tool Discovery and Execution")
        from src.agent.mcp_advisor import MCPInvestmentAdvisor
        mcp_advisor = MCPInvestmentAdvisor()
        discovered_tools = mcp_advisor._discover_tools()
        tools_config = [Tool(function_declarations=discovered_tools)] if discovered_tools else []
    else:
        logger.info("🏢 Using Direct Function Calling (Standard Mode)")
        tools_config = [invest_tool]

    model = GenerativeModel(
        model_name,
        tools=tools_config,
        system_instruction=system_instruction
    )
    
    chat = model.start_chat(response_validation=False)
    
    # Construct Dynamic Prompt
    budget = budget_override if budget_override else GOALS.get("budget", 12500)
    prompt = f"Run the bi-monthly allocation process for today. My budget is {budget} INR. My target portfolio is: {target_portfolio_str}."
    
    logger.info(f"User Prompt: {prompt}")
    
    # Helper to map function names to actual python callables
    captured_orders = []
    
    def calculate_orders_wrapper(**kwargs):
        # Determine targets dynamically if passed, else flow relies on internal logic
        t_amts = {a['ticker']: a.get('target_amount', 1e9) for a in ASSETS}
        
        results = calculate_orders(
            budget=budget,
            portfolio=kwargs.get('portfolio'),
            prices=kwargs.get('prices'),
            targets=kwargs.get('targets'),
            target_amounts=t_amts
        )
        nonlocal captured_orders
        captured_orders = results # Save for later
        logger.info(f"DEBUG: calculate_orders returned {len(results)} items.")
        return results

    function_map = {
        'get_market_snapshot': get_market_snapshot,
        'get_market_news': get_market_news,
        'check_financial_health': check_financial_health,
        'calculate_allocations': calculate_orders_wrapper
    }

    # Execute Chat Loop (Simple Automatic Function Calling)
    try:
        response = chat.send_message(prompt)
    except Exception as e:
        logger.error(f"CRITICAL ERROR sending message: {e}")
        # Ensure the error is visible in the HTTP response (stdout)
        print(f"CRITICAL AGENT ERROR: {e}") 
        traceback.print_exc()
        return
    
    # Handle Function Calls (The "Hands")
    while response.candidates and response.candidates[0].function_calls:
        function_responses = []
        
        for function_call in response.candidates[0].function_calls:
            func_name = function_call.name
            func_args = {key: val for key, val in function_call.args.items()}
            
            logger.info(f"Model requesting tool: {func_name}")
            
            if use_apigee and mcp_advisor:
                # 🛠️ EXECUTE VIA APIGEE
                try:
                    result = mcp_advisor._execute_tool(func_name, func_args)
                    
                    # Special Case: Capture orders for consolidation logic below
                    # Handle both internal name (calculate_orders) and Apigee public name (calculate-allocations)
                    if func_name in ['calculate_orders', 'calculate_allocations', 'calculate-allocations']:
                        # The tool returns a list of orders. We need to save it.
                        captured_orders = result if isinstance(result, list) else result.get('result', [])
                        logger.info(f"DEBUG: [MCP] {func_name} returned {len(captured_orders)} items.")

                    function_responses.append(
                        vertexai.generative_models.Part.from_function_response(
                            name=func_name,
                            response={"content": result}
                        )
                    )
                    logger.info(f"Tool {func_name} executed via Apigee successfully.")
                except Exception as e:
                    logger.error(f"Apigee Tool {func_name} execution failed: {e}")
                    function_responses.append(
                        vertexai.generative_models.Part.from_function_response(
                            name=func_name,
                            response={"content": {"error": str(e)}}
                        )
                    )
            else:
                # 🏢 EXECUTE DIRECTLY
                if func_name in function_map:
                    try:
                        result = function_map[func_name](**func_args)
                        
                        # Ensure result is serializable
                        if not isinstance(result, (dict, list, str, int, float, bool)):
                            result = {"result": str(result)}
                        elif not isinstance(result, dict):
                            result = {"result": result}
                            
                        function_responses.append(
                            vertexai.generative_models.Part.from_function_response(
                                name=func_name,
                                response={"content": result}
                            )
                        )
                        logger.info(f"Tool {func_name} executed successfully.")
                    except Exception as e:
                        logger.error(f"Tool {func_name} execution failed: {e}")
                        function_responses.append(
                            vertexai.generative_models.Part.from_function_response(
                                name=func_name,
                                response={"content": {"error": str(e)}}
                            )
                        )
                else:
                    logger.error(f"Unknown function requested: {func_name}")
        
        if not function_responses:
            break
        
        # Capture thoughts...
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                logger.info(f"AGENT THOUGHT: {part.text}")
                print(f"AGENT THOUGHT: {part.text}") 

        # Send back to model
        response = chat.send_message(function_responses)

    # --- FINAL Turn Enforcement ---
    # Ensure the model actually provides the final JSON list if it just called tools
    if not any(hasattr(p, "text") and ("[" in p.text) for p in response.candidates[0].content.parts):
        logger.info("🤖 Requesting final JSON summary from Agent...")
        response = chat.send_message("Excellent research. Now, provide the FINAL JSON array for all 30 tickers as per the required output format. No text before or after.")

    # Final Plan Formatting
    try:
        plan_text = response.text if hasattr(response, "text") else ""

        # Always output all parts to logs for transparency
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    logger.info(f"AGENT FINAL THOUGHT: {part.text}")
                    print(f"AGENT FINAL THOUGHT: {part.text}")

        # Logic: If we captured valid orders from the tool, use those!
        # BUT: Enrich them with AI Rationale from the plan_text JSON if available
        if auto_execute:
            final_trade_list = []
            print("DEBUG: Analysis auto-execute triggered.")
            try:
                from src.utils.llm_helpers import parse_structured_text, normalize_ticker

                # 1. Start with the FULL analysis from AI Reasoner
                ai_recommendations = extract_json_from_text(plan_text)
                
                # FALLBACK: If JSON extraction fails, try parsing structured text
                if not ai_recommendations or not isinstance(ai_recommendations, list):
                    logger.warning("JSON extraction failed. Attempting fallback text parsing.")
                    ai_recommendations = parse_structured_text(plan_text)
                
                if not ai_recommendations:
                    ai_recommendations = []
                    logger.warning("No recommendations extracted from AI.")

                # 2. Map tool-captured clinical orders for merging (Normalization aware)
                tool_map_norm = {normalize_ticker(o["ticker"]): o for o in captured_orders if "ticker" in o}
                
                # 3. Consolidate into a map by normalized ticker
                consolidated = {}
                for rec in ai_recommendations:
                    t_raw = rec.get("ticker")
                    t_norm = normalize_ticker(t_raw)
                    if t_norm:
                        # Ensure fields are valid strings/ints
                        rec["ticker"] = t_raw
                        rec["signal"] = rec.get("signal", "HOLD") or "HOLD"
                        rec["reason"] = rec.get("reason", "No detailed rationale provided.") or "No rationale."
                        rec["quantity"] = int(rec.get("quantity", 0) or 0)
                        
                        if t_norm in tool_map_norm:
                            tool_match = tool_map_norm[t_norm]
                            # Tool results (math) OVERRIDE AI recommendations for 'quantity'
                            rec["quantity"] = int(tool_match.get("quantity", 0) or 0)
                            if rec["quantity"] > 0:
                                rec["signal"] = "BUY"
                            elif rec["signal"] == "HOLD" and tool_match.get("signal") == "ACCUMULATE":
                                rec["signal"] = "ACCUMULATE"

                        consolidated[t_norm] = rec
                
                # Add tool-only tickers that AI might have missed
                for t_norm, tool_order in tool_map_norm.items():
                    if t_norm not in consolidated:
                        tool_order["reason"] = tool_order.get("reason", "Mathematical rebalance hit target.")
                        consolidated[t_norm] = tool_order

                # 4. UNIVERSAL COVERAGE: Ensure every ticker in the universe is present
                # This prevents "No Analysis" placeholders in the dashboard
                final_trade_list = []
                universe_assets = UNIVERSE_CONFIG.get("assets", [])
                
                for asset in universe_assets:
                    t_orig = asset["ticker"] # e.g. NSE:RELIANCE
                    t_norm = normalize_ticker(t_orig)
                    
                    if t_norm in consolidated:
                        item = consolidated[t_norm]
                        # Restore original ticker with prefix for dashboard consistency
                        item["ticker"] = t_orig
                        final_trade_list.append(item)
                    else:
                        # Fallback for tickers the AI skipped completely
                        final_trade_list.append({
                            "ticker": t_orig,
                            "signal": "HOLD",
                            "reason": "AI did not flag a specific action for this asset. Defaulting to HOLD.",
                            "quantity": 0
                        })
                
                print(f"DEBUG: Final consolidated trade list size: {len(final_trade_list)}")
                
                # --- APPLY USER RULES ---
                # 1. Full Analysis: Contains ALL tickers (for Dashboard UI)
                full_analysis_list = final_trade_list
                
                # 2. Execution Orders: Only Qty > 0 (for Order Pusher)
                execution_orders = [o for o in final_trade_list if o.get("quantity", 0) > 0]
                
                print(f"DEBUG: Active Orders: {len(execution_orders)}")
                
                status = save_draft_proposal(
                    orders=execution_orders, 
                    audit_trail=plan_text, 
                    merge=(specific_tickers is not None),
                    full_analysis=full_analysis_list
                )
                print(f"DEBUG: Firestore save status: {status}")
                logger.info(f"\n--- PROPOSAL STATUS: {status} ---\n")
                
            except Exception as e:
                logger.error(f"Failed to consolidate research: {e}")
                traceback.print_exc()
                # Absolute Fallback: Capture orders as provided by tool
                final_trade_list = captured_orders
                status = save_draft_proposal(final_trade_list, plan_text, merge=(specific_tickers is not None))
                logger.info(f"\n--- PROPOSAL STATUS (Fallback): {status} ---\n")
            
            if not skip_notify:
                # Send Final Report via Email
                from src.utils.notifications import NotificationManager
                from src.utils.project import get_dashboard_url
                notifier = NotificationManager()
                recipient = os.environ.get("RECIPIENT_EMAIL")
                dashboard_url = get_dashboard_url()
                
                if recipient:
                    # Generate HTML Table
                    # Calculate Stats
                    total_tickers = len(UNIVERSE_CONFIG.get("assets", []))
                    buy_count = len([t for t in final_trade_list if t.get('quantity', 0) > 0])
                    
                    html_report = f"""
                    <html>
                    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center; color: white;">
                            <h1 style="margin: 0; font-size: 24px;">📊 Investment Analysis Ready</h1>
                            <p style="margin: 10px 0 0 0; opacity: 0.8;">Zerodha Invest Agent • Bi-Monthly Rebalance</p>
                        </div>
                        
                        <div style="padding: 30px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; background: white;">
                            <h3>Executive Summary</h3>
                            <p>The AI Agent has completed its analysis of {total_tickers} tickers in your universe. It recommends taking action on <b>{buy_count}</b> of them.</p>
                            
                            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                                <thead>
                                    <tr style="background-color: #f8fafc;">
                                        <th style="padding: 12px; border-bottom: 2px solid #e2e8f0; text-align: left;">Ticker</th>
                                        <th style="padding: 12px; border-bottom: 2px solid #e2e8f0; text-align: left;">Action</th>
                                        <th style="padding: 12px; border-bottom: 2px solid #e2e8f0; text-align: left;">Qty</th>
                                    </tr>
                                </thead>
                                <tbody>
                    """
                    for t in (final_trade_list if 'final_trade_list' in locals() and final_trade_list else []):
                        sig = t.get('signal', 'HOLD')
                        qty = t.get('quantity', 0)
                        # Only show actionable items or significant HOLDS in the summary table to keep it clean? 
                        # User asked for simplified. Let's show all but highlight actions.
                        
                        color = "#15803d" if qty > 0 or "BUY" in sig else "#64748b"
                        fw = "bold" if qty > 0 else "normal"
                        
                        html_report += f"""
                                    <tr>
                                        <td style="padding: 12px; border-bottom: 1px solid #f1f5f9;"><b>{t['ticker']}</b></td>
                                        <td style="padding: 12px; border-bottom: 1px solid #f1f5f9; color: {color}; font-weight: {fw};">{sig}</td>
                                        <td style="padding: 12px; border-bottom: 1px solid #f1f5f9;">{qty}</td>
                                    </tr>
                        """
                    html_report += f"""
                                </tbody>
                            </table>

                            <div style="text-align: center; margin: 40px 0;">
                                <a href="{dashboard_url}?action=approve_batch" style="background-color: #15803d; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; margin: 0 10px; display: inline-block;">✅ Approve Batch</a>
                                <a href="{dashboard_url}?action=reject_batch" style="background-color: #b91c1c; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; margin: 0 10px; display: inline-block;">🛑 Reject & Clear</a>
                            </div>
                            
                            <div style="text-align: center; margin-bottom: 30px;">
                                <a href="{dashboard_url}" style="color: #2563eb; text-decoration: underline; font-size: 0.9em;">View Full Analysis in Dashboard</a>
                            </div>

                            <hr style="border: 0; border-top: 1px solid #f1f5f9; margin: 30px 0;">
                    """
                    
                    html_report += """
                        </div>
                        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #94a3b8;">
                            © 2026 Zerodha Invest Agent (GCP Vertex AI) • Secure Financial Automation
                        </div>
                    </body>
                    </html>
                    """

                    notifier.send_gmail(
                        recipient,
                        "📈 [Personal Investment Agent] Investment Analysis Ready",
                        f"The Agent has completed the analysis.\n\nDashboard: {dashboard_url}",
                        html_body=html_report
                    )
                 
        logger.info("\n--- FINAL AGENT RESPONSE ---\n")
        logger.info(plan_text)
    except ValueError:
        # Handle cases with multiple parts (e.g. text + function call leftovers)
        logger.info("\n--- FINAL AGENT RESPONSE ---\n")
        for part in response.candidates[0].content.parts:
            if part.text:
                logger.info(part.text)

def notify_pending_proposal():
    """Sends the summary email based on the CURRENT state in Firestore."""
    load_universe_config()
    from src.utils.project import get_project_id
    project_id = get_project_id()
    db = firestore.Client(project=project_id)
    doc = db.collection("pending_orders").document("latest").get()
    
    if not doc.exists:
        print("No pending proposal found in Firestore.")
        return
        
    data = doc.to_dict()
    orders = data.get("orders", [])
    snapshot = data.get("ui_snapshot", [])
    
    # Use snapshot if available for most accurate 'current' view
    report_list = snapshot if snapshot else orders
    
    from src.utils.notifications import NotificationManager
    from src.utils.project import get_dashboard_url
    notifier = NotificationManager()
    recipient = os.environ.get("RECIPIENT_EMAIL")
    dashboard_url = get_dashboard_url()
    
    if not recipient:
        print("RECIPIENT_EMAIL not set.")
        return

    # Generate HTML (Simplified for brevity but maintaining structure)
    buy_count = len([t for t in report_list if t.get('quantity', 0) > 0 or t.get('Buy Qty', 0) > 0])
    
    html_report = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1e293b; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 24px;">📊 Investment Analysis Ready</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.8;">Zerodha Invest Agent • Bi-Monthly Rebalance</p>
        </div>
        <div style="padding: 30px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; background: white;">
            <h3>Executive Summary</h3>
            <p>Analysis complete. There are <b>{buy_count}</b> actionable items ready for your approval.</p>
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <thead>
                    <tr style="background-color: #f8fafc;">
                        <th style="padding: 12px; border-bottom: 2px solid #e2e8f0; text-align: left;">Ticker</th>
                        <th style="padding: 12px; border-bottom: 2px solid #e2e8f0; text-align: left;">Action / Signal</th>
                        <th style="padding: 12px; border-bottom: 2px solid #e2e8f0; text-align: left;">Qty</th>
                    </tr>
                </thead>
                <tbody>
    """
    for t in report_list:
        ticker = t.get('ticker') or t.get('Symbol')
        sig = t.get('signal') or t.get('AI Signal', 'HOLD')
        qty = t.get('quantity') or t.get('Buy Qty', 0)
        
        if qty == 0 and sig == 'HOLD': continue # Keep email focused

        color = "#15803d" if qty > 0 else "#64748b"
        html_report += f"""
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #f1f5f9;"><b>{ticker}</b></td>
                        <td style="padding: 12px; border-bottom: 1px solid #f1f5f9; color: {color};">{sig}</td>
                        <td style="padding: 12px; border-bottom: 1px solid #f1f5f9;">{qty}</td>
                    </tr>
        """
    
    html_report += f"""
                </tbody>
            </table>
            <div style="text-align: center; margin: 40px 0;">
                <a href="{dashboard_url}?action=approve_batch" style="background-color: #15803d; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; margin: 0 10px; display: inline-block;">✅ Approve Batch</a>
                <a href="{dashboard_url}?action=reject_batch" style="background-color: #b91c1c; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; margin: 0 10px; display: inline-block;">🛑 Reject & Reset</a>
            </div>
            <div style="text-align: center; margin-bottom: 30px;">
                <a href="{dashboard_url}" style="color: #2563eb; text-decoration: underline; font-size: 0.9em;">View Full Analysis in Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    notifier.send_gmail(
        recipient,
        "📈 [Personal Investment Agent] Investment Analysis Ready",
        f"The Agent has completed the analysis.\n\nDashboard: {dashboard_url}",
        html_body=html_report
    )
    print("Notification Sent.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--budget", type=float, default=None)
    parser.add_argument("--tickers", type=str, default=None, help="Comma separated tickers to retry")
    parser.add_argument("--skip-notify", action="store_true", help="Skip sending email at end of analysis")
    parser.add_argument("--notify", action="store_true", help="Only send notification for current pending proposal")
    args = parser.parse_args()
    
    if args.notify:
        notify_pending_proposal()
    else:
        specific = args.tickers.split(",") if args.tickers else None
        run_agent(auto_execute=args.auto, budget_override=args.budget, specific_tickers=specific, skip_notify=args.skip_notify)
