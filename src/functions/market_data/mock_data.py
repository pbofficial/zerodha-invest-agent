
"""
Mock data for testing market data function without live API connection.
"""

MOCK_HOLDINGS = [
    {
        "tradingsymbol": "RELIANCE",
        "exchange": "NSE",
        "instrument_token": 738561,
        "isin": "INE002A01018",
        "product": "CNC",
        "price": 0,  # Average price
        "quantity": 10,
        "used_quantity": 0,
        "t1_quantity": 0,
        "realised_quantity": 10,
        "authorised_quantity": 0,
        "opening_quantity": 10,
        "short_quantity": 0,
        "collateral_quantity": 0,
        "collateral_type": "",
        "discrepancy": False,
        "average_price": 2400.0,
        "last_price": 2500.0,
        "close_price": 2450.0,
        "pnl": 1000.0,
        "day_change": 50.0,
        "day_change_percentage": 2.04
    },
    {
        "tradingsymbol": "INFY",
        "exchange": "NSE",
        "instrument_token": 408065,
        "isin": "INE009A01021",
        "product": "CNC",
        "price": 0,
        "quantity": 5,
        "used_quantity": 0,
        "t1_quantity": 0,
        "realised_quantity": 5,
        "authorised_quantity": 0,
        "opening_quantity": 5,
        "short_quantity": 0,
        "collateral_quantity": 0,
        "collateral_type": "",
        "discrepancy": False,
        "average_price": 1400.0,
        "last_price": 1450.0,
        "close_price": 1420.0,
        "pnl": 250.0,
        "day_change": 30.0,
        "day_change_percentage": 2.11
    }
]

MOCK_PRICES = {
    "RELIANCE": {
        "instrument_token": 738561,
        "last_price": 2505.0,
        "ohlc": {"open": 2460.0,"high": 2510.0,"low": 2455.0,"close": 2450.0},
        "change": 2.24,
        "depth": {"buy": [{"quantity": 100}], "sell": [{"quantity": 100}]} # Added depth for safety checks
    },
    "INFY": {
        "instrument_token": 408065,
        "last_price": 1455.0,
        "ohlc": {"open": 1425.0,"high": 1460.0,"low": 1420.0,"close": 1420.0},
        "change": 2.46,
        "depth": {"buy": [{"quantity": 100}], "sell": [{"quantity": 100}]}
    },
    "TCS": {
        "instrument_token": 2953217,
        "last_price": 3500.0,
        "ohlc": {"open": 3480.0,"high": 3520.0,"low": 3470.0,"close": 3450.0},
        "change": 1.45,
        "depth": {"buy": [{"quantity": 100}], "sell": [{"quantity": 100}]}
    },
    "HDFCBANK": {
        "last_price": 1600.0,
        "ohlc": {"close": 1590.0},
        "depth": {"buy": [{"quantity": 100}], "sell": [{"quantity": 100}]}
    },
    "KPITTECH": {
        "last_price": 1500.0,
        "ohlc": {"close": 1480.0},
        "depth": {"buy": [{"quantity": 100}], "sell": [{"quantity": 100}]}
    },
    "ZOMATO": {
        "last_price": 150.0,
        "ohlc": {"close": 148.0},
        "depth": {"buy": [{"quantity": 100}], "sell": [{"quantity": 100}]}
    },
    "NIFTYBEES": {
        "last_price": 250.0,
        "ohlc": {"close": 248.0},
        "depth": {"buy": [{"quantity": 100}], "sell": [{"quantity": 100}]}
    },
    "LIQUIDBEES": {
        "last_price": 1000.0,
        "ohlc": {"close": 1000.0},
        "depth": {"buy": [{"quantity": 100}], "sell": [{"quantity": 100}]}
    }
}
