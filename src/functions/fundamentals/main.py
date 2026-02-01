
import yfinance as yf
import logging
import json
import os
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YFINANCE_MAP removed in Phase 3
YFINANCE_MAP = {}

def check_financial_health(ticker: str):
    """
    Fetches quarterly financials from Yahoo Finance and checks for profit trends.
    
    Args:
        ticker (str): NSE Ticker symbol (e.g. 'HDFCBANK')
        
    Returns:
        dict: {'status': 'OK'|'WARNING', 'reason': str}
    """
    
    # Normalize ticker (remove exchange prefixes)
    clean_ticker = ticker.split(':')[-1].upper() if ':' in ticker else ticker.upper()
    yf_symbol = f"{clean_ticker}.NS" if not (clean_ticker.endswith(".NS") or clean_ticker.endswith(".BO")) else clean_ticker

    try:
        logger.info(f"Fetching financials for {ticker} ({yf_symbol})")
        stock = yf.Ticker(yf_symbol)
        
        # DataFrame: columns are dates (Newest -> Oldest), Index includes 'Net Income'
        financials = stock.quarterly_financials
        
        if financials.empty:
             logger.warning(f"No financials found for {ticker}")
             # Check if ETF (often has no P&L) -> OK
             if 'BEES' in ticker:
                 return {'status': 'OK', 'reason': 'ETF/Index - No P&L'}
             return {'status': 'OK', 'reason': 'Data Not Found'}

        # Find Net Income row
        # yfinance often uses 'Net Income' or 'Net Income Common Stockholders'
        row_name = 'Net Income'
        if row_name not in financials.index:
             if 'Net Income Common Stockholders' in financials.index:
                 row_name = 'Net Income Common Stockholders'
             elif 'Net Income Continuous Operations' in financials.index:
                 row_name = 'Net Income Continuous Operations'
             else:
                 return {'status': 'OK', 'reason': 'Net Income row missing'}
        
        # Get latest 3 quarters
        # Columns are usually dates desc. We take first 3.
        recent_data = financials.loc[row_name].head(3)
        
        if len(recent_data) < 3:
            return {'status': 'OK', 'reason': 'Insufficient Data'}
            
        q1 = recent_data.iloc[0] # Latest
        q2 = recent_data.iloc[1] # Prev
        q3 = recent_data.iloc[2] # Prev-Prev
        
        # Handle NaN
        if pd.isna(q1) or pd.isna(q2) or pd.isna(q3):
             return {'status': 'OK', 'reason': 'Data gaps (NaN)'}

        logger.info(f"{ticker} Recent Profits: {q1}, {q2}, {q3}")
        
        # Rule: Down sequentially for 2 quarters
        # Q2 < Q3  AND  Q1 < Q2
        if q1 < q2 and q2 < q3:
            return {'status': 'WARNING', 'reason': 'Declining Profit (2 Qtrs)'}
            
        return {'status': 'OK'}

    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {e}")
        return {'status': 'OK', 'reason': f'Error: {e}'}

if __name__ == "__main__":
    # Test run
    print(check_financial_health("HDFCBANK"))
    print(check_financial_health("ZOMATO"))
