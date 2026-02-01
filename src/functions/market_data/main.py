
import os
import json
import logging
import yfinance as yf
from kiteconnect import KiteConnect
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import pandas_market_calendars as mcal
from datetime import datetime
import pytz
from src.utils.secrets import get_secret

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration & Caching ---
METADATA_CACHE_PATH = os.path.join(os.path.dirname(__file__), "metadata_cache.json")

def load_cache():
    if os.path.exists(METADATA_CACHE_PATH):
        try:
            with open(METADATA_CACHE_PATH, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_cache(cache):
    try:
        with open(METADATA_CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=4)
    except: pass

def map_ticker_to_yf(ticker: str) -> str:
    """Maps Zerodha symbols to Yahoo Finance symbols."""
    # Special Mappings for REITs and hyphenated symbols
    REIT_MAP = {
        "EMBASSY-RR": "EMBASSY.NS",
        "MINDSPACE-RR": "MINDSPACE.NS",
        "BIRET-RR": "BIRET.NS"
    }
    if ticker in REIT_MAP:
        return REIT_MAP[ticker]

    if ":" in ticker:
        exchange, symbol = ticker.split(":")
        if exchange == "NSE":
            return f"{symbol}.NS"
        elif exchange == "BSE":
            return f"{symbol}.BO"
        return symbol
    
    # Default to NSE if no exchange specified
    return f"{ticker}.NS" if not (ticker.endswith(".NS") or ticker.endswith(".BO")) else ticker

def classify_cap(market_cap):
    """Classifies Indian market cap into Large/Mid/Small (Base in INR)."""
    if not market_cap or market_cap == 0: return "Mid" # Default to Mid if unknown, safer than Unknown
    # Thresholds (approximate Cr): Large > 20000 Cr, Mid 5000-20000 Cr
    # Updated AMFI-like thresholds for 2024-25: 
    # Large: > 60,000 Cr, Mid: 15,000 - 60,000 Cr, Small: < 15,000 Cr
    cr_value = market_cap / 10000000 # 1 Cr = 10^7
    if cr_value > 60000: return "Large"
    elif cr_value > 15000: return "Mid"
    else: return "Small"

# --- Kite Handlers ---

def get_kite_client():
    api_key = get_secret("KITE_API_KEY")
    access_token = get_secret("KITE_ACCESS_TOKEN")
    if not api_key: return None
    kite = KiteConnect(api_key=api_key)
    if access_token: kite.set_access_token(access_token)
    return kite

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
def fetch_holdings_with_retry(kite):
    return kite.holdings()

def is_market_open():
    """Checks if the Indian market (NSE) is open or a holiday/weekend."""
    try:
        now_ist = datetime.now(pytz.timezone('Asia/Kolkata'))
        nse = mcal.get_calendar('NSE')
        # Check today
        schedule = nse.schedule(start_date=now_ist.date(), end_date=now_ist.date())
        if schedule.empty:
            return False, "Holiday/Weekend"
        
        market_open = schedule.iloc[0]['market_open'].to_pydatetime()
        market_close = schedule.iloc[0]['market_close'].to_pydatetime()
        
        if now_ist < market_open: return False, "Pre-Market"
        if now_ist > market_close: return False, "Post-Market"
        
        return True, "Open"
    except Exception as e:
        logger.error(f"Market check error: {e}")
        # Fallback to simple weekend check if library fails
        return datetime.now().weekday() < 5, "Fallback"

def is_trading_day(target_date=None):
    """Specific check for if a date is a valid NSE trading day."""
    try:
        if not target_date:
            target_date = datetime.now(pytz.timezone('Asia/Kolkata')).date()
        nse = mcal.get_calendar('NSE')
        schedule = nse.schedule(start_date=target_date, end_date=target_date)
        return not schedule.empty
    except:
        return datetime.now().weekday() < 5

# --- Main Snapshot Tool ---

def get_market_snapshot(tickers: list):
    logger.info(f"Fetching snapshot for {len(tickers)} tickers")
    
    # 1. Kite Holdings
    kite = get_kite_client()
    holdings = []
    if kite:
        try:
            holdings = fetch_holdings_with_retry(kite)
        except Exception as e:
            logger.warning(f"Kite holdings fetch failed: {e}")

    # 2. Yahoo Finance Data (Prices & Metadata)
    cache = load_cache()
    valid_prices = {}
    enriched_metadata = {}
    alerts = {}

    for ticker in tickers:
        yf_sym = map_ticker_to_yf(ticker)
        try:
            t = yf.Ticker(yf_sym)
            
            # Fetch Price (Fast)
            try:
                # Use history if fast_info fails or is incomplete
                hist = t.history(period="1d")
                if not hist.empty:
                    price = round(float(hist['Close'].iloc[-1]), 2)
                    valid_prices[ticker] = price
                else:
                    # Fallback to fast_info
                    price = round(float(t.fast_info['last_price']), 2)
                    valid_prices[ticker] = price
            except:
                logger.warning(f"Price fetch failed for {yf_sym}")
            
            # Fetch Metadata (if not in cache or generic)
            if yf_sym not in cache or cache[yf_sym].get("sector") == "Unknown":
                logger.info(f"Enriching metadata for {yf_sym}")
                info = t.info
                cache[yf_sym] = {
                    "sector": info.get("sector", "Other"),
                    "cap_type": classify_cap(info.get("marketCap", 0)),
                    "risk_beta": info.get("beta", 1.0)
                }
            
            enriched_metadata[ticker] = cache[yf_sym]
            
        except Exception as e:
            logger.error(f"Failed {yf_sym}: {e}")
            alerts[ticker] = f"DATA_ERROR: {str(e)}"

    save_cache(cache)
    
    # Check for delisted/errors
    for t in tickers:
        if t not in valid_prices:
            alerts[t] = "PRICE_MISSING"

    return {
        "prices": valid_prices,
        "holdings": holdings,
        "metadata": enriched_metadata, # Added metadata for dashboard
        "alerts": alerts
    }
