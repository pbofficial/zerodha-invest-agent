
import math

def calculate_orders(budget, portfolio, prices, targets, target_amounts=None):
    """
    Calculates stock orders based on portfolio targets, budget, and absolute target amounts.
    
    Args:
        budget (float): Total investment amount.
        portfolio (list): List of holdings with 'average_price' and 'quantity'.
        prices (dict): Current market prices.
        targets (dict): Target allocation weights (0.0 to 1.0).
        target_amounts (dict, optional): Absolute target cost basis for each ticker.
    """
    
    # Helper to normalize tickers (remove exchange prefixes)
    def norm(t): return str(t).split(':')[-1].upper() if ':' in str(t) else str(t).upper()

    # Map portfolio to easier lookup with NORMALIZED tickers
    holdings_map = {norm(item['tradingsymbol']): item for item in portfolio if 'tradingsymbol' in item}
    
    # Calculate current portfolio value and filter targets
    current_holdings_value = 0.0
    asset_values = {}
    
    # Normalize input targets and prices
    norm_targets = {norm(k): v for k, v in targets.items()}
    norm_target_amounts = {norm(k): v for k, v in (target_amounts or {}).items()}
    norm_prices = {norm(k): v for k, v in prices.items()}

    analysis_results = []

    # We analyze ALL targets provided
    for ticker, weight in norm_targets.items():
        qty = 0
        price = norm_prices.get(ticker, 0)
        
        cost_basis = 0
        if ticker in holdings_map:
            h = holdings_map[ticker]
            qty = h.get('quantity', 0)
            # Cost Basis = Quantity * Avg Price
            avg_price = h.get('average_price') or h.get('average_buy_price') or price
            cost_basis = qty * avg_price
            
        current_holdings_value += (qty * price)
        
        # Determine Status wrt Target Amount
        status = "ACTIVE"
        gap = 0
        if norm_target_amounts and ticker in norm_target_amounts:
            t_amt = norm_target_amounts[ticker]
            if cost_basis >= t_amt:
                status = "MET"
            else:
                gap = t_amt - cost_basis

        analysis_results.append({
            "ticker": ticker,
            "price": price,
            "current_qty": qty,
            "current_cost": cost_basis,
            "status": status,
            "gap": gap,
            "weight": weight
        })

    # --- Step 2: Allocation Logic (Budget Based) ---
    # We still want to suggest a "Best Buys" list based on the input budget
    
    # Sort by GAP (Largest gap first)
    # Only consider ACTIVE status for auto-suggestion
    active_assets = [a for a in analysis_results if a["status"] == "ACTIVE" and a["price"] > 0]
    active_assets.sort(key=lambda x: x["gap"], reverse=True)
    
    suggestions = {}
    remaining_budget = budget
    
    # Simple Greedy Allocation to fill biggest gaps
    for asset in active_assets:
        if remaining_budget < asset["price"]:
            continue
            
        # Don't exceed the gap amount essentially (unless price is high)
        max_buy_amt = min(remaining_budget, asset["gap"])
        
        # Calculate Qty
        qty_to_buy = math.floor(max_buy_amt / asset["price"])
        
        # If gap is huge but budget is small, we just buy what we can
        if qty_to_buy == 0 and remaining_budget >= asset["price"]:
             qty_to_buy = 1 # Force at least 1 if we have budget
             
        if qty_to_buy > 0:
            suggestions[asset["ticker"]] = qty_to_buy
            remaining_budget -= (qty_to_buy * asset["price"])
            
    # --- Step 3: Format Output ---
    # Merge Analysis with Suggestions
    final_output = []
    for asset in analysis_results:
        ticker = asset["ticker"]
        s_qty = suggestions.get(ticker, 0)
        
        signal = "HOLD"
        reason = "Target Met"
        
        if asset["status"] == "ACTIVE":
            if s_qty > 0:
                signal = "BUY"
                reason = f"Top Pick. Gap: ₹{asset['gap']:.0f}"
            else:
                # It's active but we didn't afford it or it wasn't top priority
                signal = "ACCUMULATE" 
                reason = f"Underweight. Gap: ₹{asset['gap']:.0f}"
        
        final_output.append({
            "ticker": ticker,
            "signal": signal,
            "reason": reason,
            "quantity": s_qty, # Suggested Qty
            "price": asset["price"],
            "current_qty": asset["current_qty"]
        })
        
    return final_output
