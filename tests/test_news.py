
import pytest
import sys
import os

# Adjust path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.functions.news.main import get_market_news

def test_get_market_news_structure():
    """
    Test that news search returns a dictionary with the correct keys.
    Note: This is a live test against DuckDuckGo.
    """
    tickers = ["RELIANCE"]
    news = get_market_news(tickers)
    
    assert isinstance(news, dict)
    assert "RELIANCE" in news
    assert isinstance(news["RELIANCE"], list)
    
    # If results are found, verify structure
    if len(news["RELIANCE"]) > 0:
        item = news["RELIANCE"][0]
        assert "title" in item
        assert "snippet" in item
        assert "url" in item

def test_get_market_news_empty_on_fail():
    """
    Verfies that even if one ticker fails or returns nothing, 
    the function returns a valid object.
    """
    # Empty list should return empty dict
    assert get_market_news([]) == {}
