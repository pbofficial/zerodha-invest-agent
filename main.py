# Routing based on the Cloud Function name (K_SERVICE is set automatically)
def main(request):
    import os
    import sys
    import json
    
    # Add the current directory to sys.path so we can import from src
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    service_name = os.environ.get("K_SERVICE", "")
    data = request.get_json(silent=True) or {}
    
    # Robust MCP Unwrapping: If called with full MCP schema, extract parameters
    if data.get("method") == "tools/call" and "params" in data:
        data = data.get("params", {}).get("arguments", {})
    
    # 1. Specialized Agent Triggers
    if "trigger-nudge" in service_name:
        from src.agent.trigger import run_trigger as trigger_handler
        return trigger_handler(request)
    elif "morning-execution" in service_name:
        from src.agent.morning_run import run_morning_execution as morning_handler
        return morning_handler(request)
    
    # 2. Atomic Tools (The "Hands")
    elif "get-portfolio" in service_name:
        from src.functions.market_data.main import get_market_snapshot
        tickers = data.get("tickers") or data.get("ticker") or ["ALL"]
        if isinstance(tickers, str): tickers = [tickers]
        return json.dumps(get_market_snapshot(tickers))
        
    elif "check-financial-health" in service_name or "check_financial_health" in service_name:
        from src.functions.fundamentals.main import check_financial_health
        tickers = data.get("tickers") or data.get("ticker") or []
        if isinstance(tickers, str): tickers = [tickers]
        return json.dumps(check_financial_health(tickers))
        
    elif "get-market-news" in service_name or "get_market_news" in service_name:
        from src.functions.news.main import get_market_news
        tickers = data.get("tickers") or data.get("ticker") or []
        if isinstance(tickers, str): tickers = [tickers]
        return json.dumps(get_market_news(tickers))
        
    elif "calculate-allocations" in service_name:
        from src.functions.allocation.main import calculate_orders
        return json.dumps(calculate_orders(
            budget=data.get("budget", 0),
            portfolio=data.get("portfolio", []),
            prices=data.get("prices", {}),
            targets=data.get("targets", {}),
            target_amounts=data.get("target_amounts")
        ))
        
    else:
        # Default to agent handler for non-specialized routes
        from src.agent.main import main as agent_handler
        return agent_handler(request)
