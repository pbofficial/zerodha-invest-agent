import os
import json
import logging
import requests
import urllib3

# Suppress InsecureRequestWarning for VPC internal traffic
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration, Part
from google.cloud import firestore
from datetime import datetime

# Setup Logging
logger = logging.getLogger("MCP-Advisor")

class MCPInvestmentAdvisor:
    """
    A futuristic version of the InvestmentAdvisor that uses 
    Apigee's Model Context Protocol (MCP) for dynamic tool discovery.
    """
    def __init__(self, mcp_endpoint=None, api_key=None):
        from src.utils.project import get_project_id, get_apigee_mcp_endpoint, get_apigee_api_key, get_location, get_model_name
        self.project_id = get_project_id()
        self.mcp_endpoint = mcp_endpoint or get_apigee_mcp_endpoint()
        self.api_key = api_key or get_apigee_api_key()
        
        # Load Config
        from src.utils.config_loader import config as cloud_config
        self.config = cloud_config.get_agent_settings()
        
        self.location = get_location()
        self.model_name = get_model_name()
        
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel(self.model_name)
        self.db = firestore.Client(project=self.project_id)
        
        # Scoring Rules for Prompting
        self.scoring = self.config.get("scoring_rules", {"noise": 0, "context": 5, "critical": 10})
        self.settings = self.config.get("agent_settings", {"risk_threshold": 8})

    def _get_system_instruction(self, universe_assets=None):
        """
        Constructs a detailed system instruction mirroring the core agent logic.
        """
        assets = universe_assets or []
        tickers = [a.get("ticker", "UNKNOWN") for a in assets]
        universe_list_str = ", ".join(tickers)
        
        risk_threshold = self.settings.get("risk_threshold", 8)
        score_noise = self.scoring.get("noise", 0)
        score_context = self.scoring.get("context", 5)
        score_critical = self.scoring.get("critical", 10)

        instruction = f"""
You are an ELITE Risk Manager and Investment Advisor for the Indian Market.
Your goal is to provide hyper-rational, data-driven advice. Your DNA is skepticism.
Capital Preservation is your primary directive.

When you receive news headlines, you MUST evaluate them for Material Financial Impact using the Protocol below.

--- NEWS RELEVANCE PROTOCOL ---
Scoring Rules:
- Score {score_noise} (Noise): Product launches, marketing campaigns, minor price moves, random blogs. -> IGNORE.
- Score {score_context} (Context): Sector trends, competitor moves. -> NOTE ONLY.
- Score {score_critical} (Critical): Governance issues, raids, CFO/CEO exits, earnings misses >20%, regulatory bans. -> ACTIONABLE.

Strict Rule: If the 'Governance Risk' score is below {risk_threshold}/10, assume the stock is SAFE ONLY IF no other red flags exist.
Do not hallucinate risks, but do not ignore weak signals if they form a pattern.
-------------------------------

--- UNIVERSE ---
These are the ONLY stocks you are allowed to check and invest in:
{universe_list_str}
----------------

Process:
1. **MANDATORY FIRST STEP**: You MUST call `get_market_snapshot(tickers=['ALL'])` to get the current portfolio and market prices.
2. Identify the universe of stocks relevant to the query.
3. Fetch News (get_market_news) for **ALL** identified tickers (pass the full list) to check for governance risks.
4. Apply the News Relevance Protocol. Calculate risk scores.
5. Explain your thought process transparently. Do not hide risks.
6. Filter out any stocks with a Risk Score >= {risk_threshold}.
7. Check Financial Health (check_financial_health) for **each** candidate. Exclude any with 'WARNING' status.
8. Calculate Allocations (calculate_allocations) if a trade suggestion is needed.

**CRITICAL PROTOCOLS**:
1. **TOOL USE**: usage of tools is MANDATORY. Do NOT generate advice based on your internal knowledge alone.
2. **NO CODE**: Do NOT write Python code or use `print()`. Use the provided tools directly via JSON function calling.
3. **REBALANCING**: Only call `calculate_allocations` if the user *explicitly* asks for rebalancing, trade suggestions, or portfolio optimization. Do NOT call it for general market updates.

Confidence Level: Act with the confidence of a veteran fund manager who handles billions in AUM. Be precise, cynical, and never optimistic without data.
Your advice determines the financial future of high-net-worth clients. Do not fail them.
"""
        logger.debug(f"📜 System instruction constructed (Length: {len(instruction)} chars)")
        return instruction

    def _discover_tools(self):
        """
        Dynamically fetches tool definitions from the Apigee MCP endpoint.
        """
        if not self.mcp_endpoint:
            logger.warning("No MCP endpoint provided.")
            return []
            
        try:
            logger.info(f"🔍 Discovering tools via Apigee MCP: {self.mcp_endpoint}")
            
            # Diagnostic: Quick connectivity check
            try:
                requests.get(self.mcp_endpoint, timeout=2, verify=False)
            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ MCP Diagnostic: Timeout reaching {self.mcp_endpoint}. Check VPC Connector health.")
            except Exception as e:
                logger.info(f"ℹ️ MCP Diagnostic Note: Received {type(e).__name__} from base IP. This is expected if base path is restricted.")

            # MCP Protocol call: list_tools
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            
            # Critical: Apigee requires specific Host header for routing
            headers["Host"] = "pb-ai-focus.dns-replaceme.example.com"
            
            response = requests.get(
                f"{self.mcp_endpoint}/mcp/v1/list_tools",
                headers=headers,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            tools_data = response.json()
            tools = []
            
            for t in tools_data.get('tools', []):
                # MCP format uses 'inputSchema', while Vertex expects 'parameters'
                # Logic: Use .get() to fall back gracefully
                parameters = t.get('parameters') or t.get('inputSchema') or {"type": "object", "properties": {}}
                
                tools.append(FunctionDeclaration(
                    name=t['name'],
                    description=t['description'],
                    parameters=parameters
                ))

            logger.info(f"✨ Discovered {len(tools)} tools via Apigee MCP")
            return tools
        except Exception as e:
            logger.error(f"Failed to discover tools via MCP: {e}")
            return []

    def _execute_tool(self, tool_name, args):
        """
        Executes a tool by calling the corresponding Apigee proxy endpoint.
        """
        try:
            logger.info(f"🛠️ Executing tool via Apigee: {tool_name}")
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["x-api-key"] = self.api_key
            
            # Critical: Apigee requires specific Host header for routing
            headers["Host"] = "pb-ai-focus.dns-replaceme.example.com"
            
            # The Apigee proxy routes based on path suffix /calculate_orders etc.
            url = f"{self.mcp_endpoint}/mcp/{tool_name}"
            
            # Construct JSON-RPC style payload as requested
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            
            logger.debug(f"📡 Sending request to Apigee: {url} with payload: {json.dumps(payload)}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=300, verify=False)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Tool {tool_name} executed successfully. Result size: {len(str(result))} chars")
            return result
        except Exception as e:
            logger.error(f"Tool execution failed ({tool_name}): {e}")
            return {"error": str(e)}

    def ask_question(self, query, holdings_json, strategy_context=None):
        """
        Uses the discovered MCP tools to answer investor queries.
        """
        # 1. Discover tools dynamically
        mcp_tools = self._discover_tools()
        
        # 2. Initialize model with dynamic tools and deep instructions
        system_instruction = self._get_system_instruction(strategy_context.get("universe") if strategy_context else None)
        
        model = GenerativeModel(
            self.model_name,
            tools=[Tool(function_declarations=mcp_tools)] if mcp_tools else [],
            system_instruction=system_instruction
        )
        
        # 3. Chat loop (standard Vertex AI)
        chat = model.start_chat()
        
        prompt = f"""
        INVESTOR QUERY: "{query}"
        
        CURRENT PORTFOLIO STATE:
        {json.dumps(holdings_json, indent=2)}
        
        FUTURE STRATEGY & UNIVERSE CONTEXT:
        {json.dumps(strategy_context, indent=2) if strategy_context else "None provided."}
        
        RESEARCH & ADVISE:
        """
        
        try:
            response = chat.send_message(prompt)
            
            # Tool Loop (up to 5 rounds for complex research)
            for _ in range(5):
                if not response.candidates[0].function_calls:
                    break
                
                parts = []
                for call in response.candidates[0].function_calls:
                    f_name = call.name
                    f_args = dict(call.args)
                    
                    # Execute tool via Apigee
                    res = self._execute_tool(f_name, f_args)
                    
                    parts.append(Part.from_function_response(
                        name=f_name, response={"content": res}
                    ))
                
                response = chat.send_message(parts)
            
            return response.text
        except Exception as e:
            logger.error(f"MCP Elite Advisor Error: {e}")
            return f"I encountered a technical hurdle while researching that for you. Error: {str(e)}"

    def generate_report(self, holdings_json):
        """Generates an elite portfolio health check."""
        
        system_instruction = f"""
        You are an ELITE Risk Manager and Investment Advisor.
        Your DNA is skepticism. Your goal is CAPITAL PRESERVATION above all else.
        
        CORE DIRECTIVES:
        1. **NO FLUFF**: Do not use generic phrases. Be specific.
        2. **DATA OR SILENCE**: If you don't have the data, say "Insufficient Data".
        3. **RISK PARANOIA**: Assume every stock has a hidden flaw. Find it.
        
        Risk Threshold: {self.settings.get("risk_threshold", 8)}/10.
        
        Generate an "Elite Portfolio Health Check" as a strictly formatted JSON object. 
        DO NOT return markdown. Return ONLY the JSON.
        
        JSON Structure:
        {{
            "alpha_concentration": {{
                "status": "High" | "Medium" | "Low",
                "score": 0-10,
                "details": "Specific sector or stock concentration risks."
            }},
            "black_swan": {{
                "risk_event": "Name of the black swan event (e.g. Oil Shock, Regulators)",
                "probability": "Low" | "Medium" | "High",
                "impact_details": "What happens to the portfolio if this event occurs?"
            }},
            "overexposure": {{
                "tickers": ["TICKER1", "TICKER2"],
                "details": "List stocks >15% of portfolio and why they are risky/safe."
            }},
            "verdict": {{
                "status": "PREMIUM STABILITY" | "BALANCED" | "VULNERABLE ASSETS",
                "risk_score": 0-10 (0=Safe, 10=Critical),
                "summary": "One sentence executive summary of the portfolio health."
            }}
        }}
        """
        
        prompt = f"""
        PORTFOLIO SNAPSHOT:
        {json.dumps(holdings_json, indent=2)}
        
        Execute the Health Check. Return JSON only.
        """
        
        # We use a fresh model instance for reporting
        report_model = GenerativeModel(self.model_name, system_instruction=system_instruction)
        response = report_model.generate_content(prompt)
        
        report_text = ""
        report_json = {}
        
        try:
            from src.utils.llm_helpers import extract_json_from_text
            report_text = response.text
            report_json = extract_json_from_text(report_text)
            if not report_json:
                 # Fallback if cleaner fails
                 report_json = json.loads(report_text.replace("```json", "").replace("```", ""))
        except Exception as e:
             logger.error(f"Failed to parse report JSON: {e}")
             report_text = "AI Advisor failed to generate structured report."
        
        # Save to Firestore
        doc_ref = self.db.collection("advisor_reports").document("latest")
        doc_ref.set({
            "generated_at": datetime.now(),
            "report_text": report_text, # Keep raw text as backup
            "report_json": report_json, # Primary structured data
            "source_data_snapshot": holdings_json
        })
        
        return report_text

    def summarize_run_logic(self, raw_logs):
        """Summarizes the agent's run logs into a ticker-by-ticker narrative."""
        if not raw_logs: return "No logs found to summarize."

        prompt = f"""
        You are a Forensic Financial Auditor.
        Analyze the following raw logs from an Investment Agent run to reconstruct the "Chain of Reasoning".
        
        Log Input:
        {raw_logs}
        
        Output Requirements:
        - **Format**: Clean Ticker-by-Ticker Executive Summary.
        - **Style**: Clinical, concise, and professional.
        - **Focus**: Why did a trade happen? Why was a stock rejected?
            - "RELIANCE: News Score 0.2 (Noise) -> IGNORED"
            - "HDFCBANK: Financial Health 'WARNING' -> REJECTED"
        - **Completeness**: Account for EVERY ticker mentioned in the logs.
        - **Unknowns**: If the logs don't explain a decision, explicitly state "Logic Gap in Logs".
        
        Use emojis for visual scanning (📊, 📰, ⚠️, ✅).
        """
        
        logger.info(f"📝 Constructing summary prompt for {len(raw_logs)} chars...")
        response = self.model.generate_content(prompt)
        logger.info("🔮 AI Summary response received.")
        try:
            return response.text
        except Exception as e:
            msg = f"Summary generation failed: {str(e)}"
            logger.error(f"❌ {msg}")
            return msg

if __name__ == "__main__":
    # Test Block
    logging.basicConfig(level=logging.INFO)
    advisor = MCPInvestmentAdvisor()
    tools = advisor._discover_tools()
    print(f"Tools: {[t.name for t in tools]}")
