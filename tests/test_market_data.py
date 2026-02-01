
import os
import sys
import json
import logging
import unittest

# Add the project root to sys.path to allow imports
# Assuming structure:
# root/
#   src/functions/market_data/main.py
#   tests/test_market_data.py

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# We need to target the specific function directory for the import to work 
# given how main.py manages its own imports (local mock_data)
# But main.py does "from .mock_data import..." which works if imported as a package
# OR "from mock_data" if run directly. 
# Let's import it via full path.

sys.path.insert(0, os.path.join(project_root, 'src', 'functions', 'market_data'))

import main as market_data_main
get_market_snapshot = market_data_main.get_market_snapshot

class TestMarketData(unittest.TestCase):
    
    def setUp(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        # Force Mock Mode
        os.environ["USE_MOCK_DATA"] = "True"
        # Clear API keys to ensure we use mock
        if "KITE_API_KEY" in os.environ:
            del os.environ["KITE_API_KEY"]

    def test_get_market_snapshot_mock(self):
        print("\nTesting get_market_snapshot with MOCK data...")
        
        tickers = ["RELIANCE", "INFY", "TCS"]
        data = get_market_snapshot(tickers)
        
        print("Data received:", json.dumps(data, indent=2))
        
        self.assertIn("prices", data)
        self.assertIn("holdings", data)
        self.assertIsInstance(data["holdings"], list)
        self.assertIn("RELIANCE", data["prices"])

if __name__ == "__main__":
    unittest.main()
