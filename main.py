
# Routing based on the Cloud Function name (K_SERVICE is set automatically)
def main(request):
    import os
    import sys
    
    # Add the current directory to sys.path so we can import from src
    # This is done inside main to ensure the container starts fast
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir not in sys.path:
        sys.path.append(root_dir)

    service_name = os.environ.get("K_SERVICE", "")
    
    if "trigger-nudge" in service_name:
        from src.agent.trigger import run_trigger as trigger_handler
        return trigger_handler(request)
    elif "morning-execution" in service_name:
        from src.agent.morning_run import run_morning_execution as morning_handler
        return morning_handler(request)
    else:
        # Default to agent handler for portfolio, allocations, and trade functions
        from src.agent.main import main as agent_handler
        return agent_handler(request)
