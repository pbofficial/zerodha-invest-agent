
import logging
from duckduckgo_search import DDGS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import concurrent.futures

def _fetch_ticker_news(ticker):
    """Helper to fetch news for a single ticker."""
    news_items = []
    seen_urls = set()
    clean_ticker = ticker.split(':')[-1] if ':' in ticker else ticker
    
    queries = [
        f"{clean_ticker} fraud investigation raid",
        f"{clean_ticker} SEBI penalty regulatory action",
        f"{clean_ticker} CEO resignation management exit",
        f"{clean_ticker} quarterly results profit drop"
    ]
    
    try:
        # DDGS context manager is not thread-safe if shared, so instantiate per thread or use outside?
        # DDGS documents say it's better to instantiate one object if possible, but for threads safer to use fresh or context?
        # To be safe and simple: Instantiate fresh DDGS() for each ticker is robust but maybe slower connect time.
        # However, DDGS() usually uses requests Session. 
        # Let's try instantiating per thread.
        with DDGS() as ddgs:
            for query in queries:
                try:
                    # timelimit='w' restricts to past week (7 days)
                    results = ddgs.text(query, max_results=2, timelimit="w")
                    for r in results:
                        url = r.get("href")
                        if url and url not in seen_urls:
                            news_items.append({
                                "title": r.get("title"),
                                "snippet": r.get("body"),
                                "url": url
                            })
                            seen_urls.add(url)
                except Exception as q_e:
                    # Individual query failure should not fail the whole ticker
                    continue
                    
    except Exception as e:
        logger.error(f"Error searching for {ticker}: {e}")
        
    if not news_items:
        return ticker, [{
            "title": "No Material News",
            "snippet": "No significant negative news found regarding fraud, SEBI actions, management, or profit drops.",
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
