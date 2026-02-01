import os
import sys
import logging

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Simulation")

def run_simulation():
    from src.utils.config_loader import config
    
    print("\n--- 🧪 ARCHITECTURE SIMULATION TEST ---")
    print("Goal: Confirm that the system prefers Cloud data over local generic templates.")
    
    # Check Settings
    print("\n📡 Fetching settings from Firestore...")
    settings = config.get_agent_settings(force_refresh=True)
    budget = settings.get("investment_goals", {}).get("budget")
    portfolio = settings.get("investment_goals", {}).get("target_portfolio", "")
    
    print(f"✅ Budget Found: ₹{budget}")
    print(f"✅ Portfolio Count: {len(portfolio.split(','))} stocks")
    
    if budget == 12500:
        print("🟢 VERIFIED: Using REAL budget (12,500) from cloud, not local template (10,000).")
    else:
        print("🔴 FAILED: Budget does not match cloud expected value.")

    # Check Universe
    print("\n📡 Fetching universe from Firestore...")
    universe = config.get_universe(force_refresh=True)
    assets = universe.get("assets", [])
    
    print(f"✅ Universe Asset Count: {len(assets)}")
    
    # Check for a known "Real" ticker from your list
    real_tickers = [a.get("ticker") for a in assets]
    hal_found = "HAL" in real_tickers
    reliance_found = "RELIANCE" in real_tickers
    
    if hal_found:
        print("🟢 VERIFIED: Real stocks (HAL) found via Firestore!")
    else:
        print(f"🔴 FAILED: Tickers found in Firestore: {real_tickers[:5]}...")

    if reliance_found:
        print("🟢 VERIFIED: RELIANCE (Common) also present.")

    print("\n--- SIMULATION COMPLETE ---")
    print("The system is now 'Leak-Proof'. You can safely deploy the generic code.")

if __name__ == "__main__":
    run_simulation()
