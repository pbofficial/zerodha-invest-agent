
import pytest
import sys
import os

# Adjust path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.functions.allocation.main import calculate_orders

def test_standard_allocation():
    """
    Test standard mode where prices are low enough for slots.
    Budget: 12500 -> Slot: 2500
    Prices: 1000, 500...
    Should buy multiple units.
    """
    budget = 12500
    portfolio = [] # Empty portfolio
    prices = {
        'TATASTEEL': 100,
        'ITC': 200, 
        'SBI': 500,
        'INFY': 1000,
        'RELIANCE': 2000
    }
    targets = {
        'TATASTEEL': 0.2, # 2500 target
        'ITC': 0.2,
        'SBI': 0.2,
        'INFY': 0.2,
        'RELIANCE': 0.2
    }
    
    target_amounts = {k: v * budget for k, v in targets.items()}
    
    orders = calculate_orders(budget, portfolio, prices, targets, target_amounts)
    
    print("\n[Standard] Orders:", orders)
    
    # Check if we got orders for all
    assert len(orders) == 5
    
    # Check quantities
    # Slot = 2500
    # RELIANCE (2000): floor(2500/2000) = 1
    # INFY (1000): floor(2500/1000) = 2
    
    rel_order = next(o for o in orders if o['ticker'] == 'RELIANCE')
    assert rel_order['quantity'] == 1
    
    inf_order = next(o for o in orders if o['ticker'] == 'INFY')
    assert inf_order['quantity'] == 2

def test_high_price_fix_concentrated_mode():
    """
    Test scenario where Top Asset Price > Slot Amount.
    Budget: 12500 -> Slot: 2500
    Top Asset (MARUTI): 10000
    
    Standard logic would give 0 qty. 
    High Price Fix should dedicate budget to buy 1.
    """
    budget = 12500
    portfolio = []
    prices = {
        'MARUTI': 10000, # Very high price, > 2500 slot
        'ITC': 200,
        'TATASTEEL': 100
    }
    targets = {
        'MARUTI': 0.5, # Huge target, so it will be rank #1
        'ITC': 0.25,
        'TATASTEEL': 0.25
    }
    
    orders = calculate_orders(budget, portfolio, prices, targets)
    
    print("\n[Concentrated] Orders:", orders)
    
    # Verify MARUTI is in orders with qty 1
    maruti_order = next((o for o in orders if o['ticker'] == 'MARUTI'), None)
    
    assert maruti_order is not None, "MARUTI should be ordered in Concentrated Mode"
    assert maruti_order['quantity'] == 1
    assert "Top Pick" in maruti_order['reason']
    
    # Check remaining budget logic (Greedy fill)
    # Spent 10000 on MARUTI. Remaining: 2500.
    # Should buy ITC (200) -> 1 unit? 
    # Logic implies: "If funds remain, move to #2" -> Buy 1 unit of #2.
    
    itc_order = next((o for o in orders if o['ticker'] == 'ITC'), None)
    if itc_order:
        assert itc_order['quantity'] == 1

def test_ranking_logic():
    """
    Verify sorting by underweight %.
    """
    budget = 10000
    portfolio = []
    prices = {'A': 100, 'B': 100}
    
    # A is 80% allocation, B is 20%
    targets = {'A': 0.8, 'B': 0.2}
    
    orders = calculate_orders(budget, portfolio, prices, targets)
    
    # A should be first because it has highest target (and 0 current holdings)
    assert orders[0]['ticker'] == 'A'
