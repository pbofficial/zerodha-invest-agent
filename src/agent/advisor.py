
import os
import json
import logging
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
from google.cloud import firestore
from datetime import datetime

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Advisor")

class InvestmentAdvisor:
    def __init__(self):
        from src.utils.project import get_project_id
        self.project_id = get_project_id()
        
        # Load Config via Unified Cloud Loader
        from src.utils.config_loader import config as cloud_config
        try:
            self.config = cloud_config.get_agent_settings()
            settings = self.config.get("agent_settings", {})
            self.scoring = self.config.get("scoring_rules", {})
            self.goals = self.config.get("investment_goals", {})
        except Exception as e:
            logger.error(f"⚠️ Advisor config load error: {e}")
            settings = {}
            self.scoring = {}
            self.goals = {}
            self.config = {}

        self.location = os.environ.get("LOCATION", settings.get("location", "us-east4"))
        self.model_name = os.environ.get("MODEL_NAME", settings.get("model_name", "gemini-2.0-flash"))
        self.risk_threshold = settings.get("risk_threshold", 8)
        
        # Initialize Vertex AI
        logger.info(f"🧠 Advisor Initializing: Project={self.project_id} | Location={self.location} | Model={self.model_name}")
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel(self.model_name)
        self.db = firestore.Client(project=self.project_id)

    def _get_system_instruction(self, context_type="report"):
        score_noise = self.scoring.get("noise", 0)
        score_context = self.scoring.get("context", 5)
        score_critical = self.scoring.get("critical", 10)

        base_instruction = f"""
        You are an ELITE, HYPER-SUCCESSFUL Investment Agent for High Net Worth Individuals.
        You have made your clients billions of dollars by being hyper-rational, forward-thinking, and aggressive about risk.
        You do NOT sugarcoat. You are decisive and act with the confidence of a veteran fund manager.
        You strictly follow the News Relevance Protocol for any research:
        - Score {score_noise} (Noise): IGNORE.
        - Score {score_context} (Context): NOTE ONLY.
        - Score {score_critical} (Critical): ACTIONABLE.
        
        Risk Threshold: {self.risk_threshold}/10. Anything above this is unacceptable for your elite clients.
        """
        
        if context_type == "report":
            return base_instruction + """
            Generate an "Elite Portfolio Health Check".
            1. Analyze the Sector Concentration with a focus on Alpha generation.
            2. Evaluate the Risk Profile relative to global market standards.
            3. Call out any single stock that is >10% of the portfolio (Overexposure).
            4. Verdict: "PREMIUM STABILITY" or "VULNERABLE ASSETS".
            """
        elif context_type == "qa":
            return base_instruction + """
            You are a world-class Investment Agent answering direct queries.
            Use the provided context (Holdings and Future Targets) to give expert advice.
            You have access to REAL-TIME tools for market news and snapshots. If you need data to answer a question, USE YOUR TOOLS.
            Do not admit ignorance if a tool can get you the answer.
            Act as a mentor and strategist. If a user is making a mistake, tell them bluntly.
            """
        return base_instruction

    def ask_question(self, query, holdings_json, strategy_context=None):
        """Answers ad-hoc questions using tool-augmented research and elite persona."""
        from src.functions.news.main import get_market_news
        from src.functions.market_data.main import get_market_snapshot
        
        # Tools definitions for help
        from vertexai.generative_models import Tool, FunctionDeclaration
        
        news_tool = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="get_market_news",
                    description="Fetches recent news for tickers to evaluate sentiment or risk.",
                    parameters={
                        "type": "object",
                        "properties": {"tickers": {"type": "array", "items": {"type": "string"}}},
                        "required": ["tickers"]
                    }
                ),
                FunctionDeclaration(
                    name="get_market_snapshot",
                    description="Fetches current price and holdings for tickers.",
                    parameters={
                        "type": "object",
                        "properties": {"tickers": {"type": "array", "items": {"type": "string"}}},
                        "required": ["tickers"]
                    }
                )
            ]
        )

        model = GenerativeModel(
            self.model_name,
            tools=[news_tool],
            system_instruction=self._get_system_instruction("qa")
        )
        
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
            
            # Simple Tool Loop
            for _ in range(3): # Limit to 3 rounds of research
                if not response.candidates[0].function_calls: break
                
                parts = []
                for call in response.candidates[0].function_calls:
                    f_name = call.name
                    f_args = dict(call.args)
                    logger.info(f"🧠 Assistant using tool: {f_name}({f_args})")
                    
                    if f_name == "get_market_news":
                        res = get_market_news(**f_args)
                    elif f_name == "get_market_snapshot":
                        res = get_market_snapshot(**f_args)
                    else:
                        res = {"error": "Tool not found"}
                    
                    parts.append(vertexai.generative_models.Part.from_function_response(
                        name=f_name, response={"content": res}
                    ))
                
                response = chat.send_message(parts)
            
            return response.text
        except Exception as e:
            logger.error(f"Elite Advisor Error: {e}")
            return f"I encountered a technical hurdle while researching that for you. Error: {str(e)}"

    def generate_report(self, holdings_json):
        """Generates an elite portfolio health check."""
        prompt = f"""
        Here is the user's current portfolio:
        {json.dumps(holdings_json, indent=2)}
        
        Analyze this like a high-stakes fund manager. Focus on risk and capital preservation.
        """
        
        response = self.model.generate_content(
            [self._get_system_instruction("report"), prompt]
        )
        
        try:
            report_text = response.text
        except AttributeError:
             report_text = "AI Advisor failed to generate text for the report."
        
        # Save to Firestore
        doc_ref = self.db.collection("advisor_reports").document("latest")
        doc_ref.set({
            "generated_at": datetime.now(),
            "report_text": report_text,
            "source_data_snapshot": holdings_json
        })
        
        return report_text

    def summarize_run_logic(self, raw_logs):
        """Summarizes the agent's run logs into a ticker-by-ticker narrative."""
        if not raw_logs: return "No logs found to summarize."

        prompt = f"""
        Analyze the following raw logs from an Investment Agent run.
        Extract the DECISION LOGIC for EACH ticker involved.
        
        Log Input:
        {raw_logs}
        
        Output Requirements:
        - Format as a clean Ticker-by-Ticker Executive Summary.
        - Use Emojis for readability (e.g. 📊 for financials, 📰 for news).
        - Focus on "Why" the agent made its decision (e.g. "News score was 0.8 which outweighed neutral financials").
        - **DO NOT SKIP ANY TICKERS** mentioned in the logs. If a ticker from the universe is missing from the logs, note it as "Analysis Incomplete in Logs".
        - Keep it professional and concise.
        - Highlight any critical warnings or errors encountered.
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
    # Test Run
    advisor = InvestmentAdvisor()
    print("Advisor Initialized.")
