import logging
from datetime import datetime
from duckduckgo_search import DDGS
import yfinance as yf
import concurrent.futures

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _fetch_ticker_news(ticker):
    """Helper to fetch news for a single ticker with high sensitivity."""
    news_items = []
    seen_urls = set()
    
    # 1. Normalize Ticker & Get Company Name (Crucial for search hits)
    clean_ticker = ticker.split(':')[-1] if ':' in ticker else ticker
    yf_symbol = clean_ticker if clean_ticker.endswith(".NS") or clean_ticker.endswith(".BO") else f"{clean_ticker}.NS"
    
    company_name = clean_ticker
    try:
        # We only need the longName, which is usually fast
        stock = yf.Ticker(yf_symbol)
        company_name = stock.info.get("longName") or clean_ticker
        # Remove common suffixes to keep search terms broad
        company_name = company_name.replace("Limited", "").replace("Ltd", "").strip()
    except Exception as e:
        logger.warning(f"Could not fetch company name for {ticker}: {e}")

    # 2. Balanced Cynical Queries (Past 14 Days & Current Year)
    from datetime import datetime, timedelta
    now = datetime.now()
    current_year = str(now.year)
    cutoff_date = now - timedelta(days=14)
    
    queries = [
        f"{company_name} fraud {current_year}",
        f"{company_name} SEBI penalty {current_year}",
        f"{company_name} police complaint {current_year}",
        f"{company_name} investigation {current_year}",
        f"{company_name} negative news {current_year}",
        f"{clean_ticker} stock crash {current_year}"
    ]
    
    try:
        with DDGS() as ddgs:
            for query in queries:
                try:
                    # 'in-en' region for Indian market news
                    results = ddgs.news(query, region='in-en', max_results=5, timelimit="w")
                    if results:
                        for r in results:
                            url = r.get("url")
                            title = r.get("title", "")
                            snippet = r.get("body", "")
                            date_str = r.get("date", "")
                            
                            # --- STRICT RECENCY & YEAR FILTER ---
                            is_recent = True
                            if date_str:
                                try:
                                    # DDG News usually returns ISO format: 2026-02-04T12:30:00+00:00
                                    # We take the first 10 chars for YYYY-MM-DD
                                    article_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                                    if article_date < cutoff_date or article_date.year != now.year:
                                        is_recent = False
                                except Exception:
                                    pass # If date parsing fails, we fallback to text matching
                            
                            # 3. RELEVANCE & CYNICAL FILTER
                            text_body = (title + " " + snippet).lower()
                            
                            # Mandatory: Match either Company Name or Ticker (Prevents NFL/US news)
                            name_match = (company_name.lower() in text_body or 
                                         clean_ticker.lower() in text_body or
                                         ticker.lower() in text_body)
                            
                            # Indian Market Context
                            india_keywords = ["india", "sebi", "nse", "bse", "crore", "inr", "₹", "mumbai", "delhi"]
                            india_related = any(kw in text_body for kw in india_keywords)
                            
                            if url and url not in seen_urls and is_recent and name_match and india_related:
                                news_items.append({
                                    "title": title,
                                    "snippet": snippet,
                                    "url": url,
                                    "date": date_str
                                })
                                seen_urls.add(url)
                except Exception:
                    continue
                    
    except Exception as e:
        logger.error(f"Error searching for {ticker}: {e}")
        
    if not news_items:
        return ticker, [{
            "title": "No Material News",
            "snippet": f"No significant negative headlines found for {company_name} ({clean_ticker}) in the past 14 days ({current_year}).",
            "url": ""
        }]
    return ticker, news_items

def get_market_news(tickers: list):
    """
    Fetches market news in parallel chunks to avoid rate limiting.
    """
    all_news = {}
    chunk_size = 5 # Small chunks to be safe with DDG
    
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i : i + chunk_size]
        logger.info(f"Fetching news chunk: {chunk}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(chunk)) as executor:
            future_to_ticker = {executor.submit(_fetch_ticker_news, t): t for t in chunk}
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    t_symbol, results = future.result()
                    all_news[t_symbol] = results
                except Exception as exc:
                    logger.error(f"News fetch failed for {ticker}: {exc}")
                    all_news[ticker] = []
        
        # Small sleep between chunks to avoid DDG blocks
        import time
        if i + chunk_size < len(tickers):
            time.sleep(1.5)

    return all_news
