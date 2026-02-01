import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.append(project_root)

from src.functions.market_data.main import get_market_snapshot

def test_market_data():
    print("\n--- Market Data Test (Hybrid Mode) ---")
    
    # Example Tickers (Zerodha format)
    tickers = ["NSE:RELIANCE", "NSE:INFY", "NSE:TCS"]
    
    # Set Mock Mode to False to test real yfinance fetch
    os.environ["USE_MOCK_DATA"] = "False"
    # We don't necessarily need a real KITE_API_KEY for yfinance part, 
    # but the function checks for its presence to avoid mock mode.
    os.environ["KITE_API_KEY"] = "test_key" 
    
    try:
        data = get_market_snapshot(tickers)
        
        print("\n[v] Successfully fetched data!")
        print("\nPrices:")
        for ticker, price in data['prices'].items():
            print(f"  {ticker}: {price}")
            
        if data['alerts']:
            print("\nAlerts:")
            for ticker, alert in data['alerts'].items():
                print(f"  {ticker}: {alert}")
                
        print("\nNote: Holdings will be empty unless you have KITE credentials set up.")
        print(f"Holdings count: {len(data['holdings'])}")
        
    except Exception as e:
        print(f"\n[!] Test Failed: {e}")

if __name__ == "__main__":
    test_market_data()
