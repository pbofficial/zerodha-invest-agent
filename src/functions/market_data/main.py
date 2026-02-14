
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
    
    # 0. Handle 'ALL' keyword
    if tickers and (tickers == ['ALL'] or tickers[0] == 'ALL'):
        logger.info("Resolving 'ALL' tickers from Universe + Holdings...")
        try:
            from src.utils.config_loader import config
            universe = config.get_universe().get("assets", [])
            u_tickers = [a["ticker"] for a in universe]
            
            # We'll merge with holdings later, but start with universe
            tickers = u_tickers
            logger.info(f"Resolved 'ALL' to {len(tickers)} universe assets.")
        except Exception as e:
            logger.error(f"Failed to resolve universe for 'ALL': {e}")
            tickers = [] # Fallback to just holdings (added below)

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

    import concurrent.futures

    def _fetch_single_ticker(ticker, cache_ref):
        """Helper to fetch data for a single ticker."""
        yf_sym = map_ticker_to_yf(ticker)
        result = {
            "ticker": ticker,
            "price": None,
            "metadata": None,
            "alert": None
        }
        
        try:
            t = yf.Ticker(yf_sym)
            
            # Fetch Price (Fast)
            try:
                # Use history if fast_info fails or is incomplete
                hist = t.history(period="1d")
                if not hist.empty:
                    price = round(float(hist['Close'].iloc[-1]), 2)
                    result["price"] = price
                else:
                    # Fallback to fast_info
                    price = round(float(t.fast_info['last_price']), 2)
                    result["price"] = price
            except:
                logger.warning(f"Price fetch failed for {yf_sym}")
            
            # Fetch Metadata (if not in cache or generic)
            # Note: cache_ref is a copy or ref, modifying it here might be thread-unsafe if writing
            # But we are reading mostly. We will return the metadata to update the main cache safely.
            meta_data = None
            if yf_sym not in cache_ref or cache_ref[yf_sym].get("sector") == "Unknown":
                # logger.info(f"Enriching metadata for {yf_sym}")
                info = t.info
                meta_data = {
                    "sector": info.get("sector", "Other"),
                    "cap_type": classify_cap(info.get("marketCap", 0)),
                    "risk_beta": info.get("beta", 1.0)
                }
            else:
                meta_data = cache_ref[yf_sym]
            
            result["metadata"] = (yf_sym, meta_data) # Return (key, value)
            
        except Exception as e:
            logger.error(f"Failed {yf_sym}: {e}")
            result["alert"] = f"DATA_ERROR: {str(e)}"
            
        return result

    # Execute in Parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(_fetch_single_ticker, t, cache): t for t in tickers}
        
        for future in concurrent.futures.as_completed(future_to_ticker):
            try:
                res = future.result()
                t = res["ticker"]
                
                # Update Prices
                if res["price"] is not None:
                    valid_prices[t] = res["price"]
                
                # Update Metadata & Cache
                if res["metadata"]:
                    yf_sym_key, meta_val = res["metadata"]
                    # Update local cache safely (main thread)
                    cache[yf_sym_key] = meta_val
                    enriched_metadata[t] = meta_val
                
                # Update Alerts
                if res["alert"]:
                    alerts[t] = res["alert"]
                    
            except Exception as exc:
                t = future_to_ticker[future]
                logger.error(f"Snapshot thread failed for {t}: {exc}")
                alerts[t] = "THREAD_ERROR"

    save_cache(cache)
    
    # Check for delisted/errors
    for t in tickers:
        if t not in valid_prices and t not in alerts:
             alerts[t] = "PRICE_MISSING"

    return {
        "prices": valid_prices,
        "holdings": holdings,
        "metadata": enriched_metadata,
        "alerts": alerts
    }
