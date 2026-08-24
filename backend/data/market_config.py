"""
Weekly Wonders - Market Today
Central configuration: every index and commodity we track.

IMPORTANT: yfinance is not officially supported by Yahoo Finance.
Some symbols below are well-established and reliable (major US/Europe/Asia
indices, commodities futures). Others (some Indian sectoral indices) are
best-guess tickers that MUST be verified by test_symbols.py before we
build features on top of them. Do not assume any symbol works until
it's been tested.
"""

# Each asset: name, yfinance symbol, region, asset type
INDICES = {
    "India": [
        {"name": "NIFTY 50", "symbol": "^NSEI", "region": "India", "type": "index"},
        {"name": "NIFTY Next 50", "symbol": "^NSMIDCP", "region": "India", "type": "index"},
        {"name": "NIFTY Midcap 50", "symbol": "^NSEMDCP50", "region": "India", "type": "index"},
        {"name": "NIFTY 500", "symbol": "^CRSLDX", "region": "India", "type": "index"},
        {"name": "BSE SENSEX", "symbol": "^BSESN", "region": "India", "type": "index"},
        {"name": "NIFTY Bank", "symbol": "^NSEBANK", "region": "India", "type": "index"},
        {"name": "NIFTY IT", "symbol": "^CNXIT", "region": "India", "type": "index"},
        {"name": "NIFTY Auto", "symbol": "^CNXAUTO", "region": "India", "type": "index"},
        {"name": "NIFTY VIX", "symbol": "^INDIAVIX", "region": "India", "type": "index"},
    ],
    "US": [
        {"name": "S&P 500", "symbol": "^GSPC", "region": "US", "type": "index"},
        {"name": "Nasdaq-100", "symbol": "^NDX", "region": "US", "type": "index"},
        {"name": "Dow Jones Industrial Average", "symbol": "^DJI", "region": "US", "type": "index"},
        {"name": "Russell 2000", "symbol": "^RUT", "region": "US", "type": "index"},
        {"name": "VIX", "symbol": "^VIX", "region": "US", "type": "index"},
    ],
    "Europe": [
        {"name": "EURO STOXX 50", "symbol": "^STOXX50E", "region": "Europe", "type": "index"},
        {"name": "FTSE 100", "symbol": "^FTSE", "region": "Europe", "type": "index"},
        {"name": "DAX", "symbol": "^GDAXI", "region": "Europe", "type": "index"},
    ],
    "Asia": [
        {"name": "Nikkei 225", "symbol": "^N225", "region": "Asia", "type": "index"},
        {"name": "KOSPI", "symbol": "^KS11", "region": "Asia", "type": "index"},
        {"name": "Hang Seng Index", "symbol": "^HSI", "region": "Asia", "type": "index"},
    ],
}

# Commodities use futures contract tickers on Yahoo (the "=F" suffix)
COMMODITIES = [
    {"name": "Gold", "symbol": "GC=F", "region": "Global", "type": "commodity"},
    {"name": "Silver", "symbol": "SI=F", "region": "Global", "type": "commodity"},
    {"name": "Brent Crude", "symbol": "BZ=F", "region": "Global", "type": "commodity"},
    {"name": "WTI Crude", "symbol": "CL=F", "region": "Global", "type": "commodity"},
    {"name": "Natural Gas", "symbol": "NG=F", "region": "Global", "type": "commodity"},
]
# Currency pairs - format is BASE+QUOTE+"=X" for yfinance forex tickers
CURRENCIES = [
    {"name": "EUR/USD", "symbol": "EURUSD=X", "region": "Global", "type": "currency"},
    {"name": "GBP/USD", "symbol": "GBPUSD=X", "region": "Global", "type": "currency"},
    {"name": "USD/JPY", "symbol": "USDJPY=X", "region": "Global", "type": "currency"},
    {"name": "USD/INR", "symbol": "USDINR=X", "region": "Global", "type": "currency"},
    {"name": "EUR/INR", "symbol": "EURINR=X", "region": "Global", "type": "currency"},
]
# The 6 markets shown in "Global Market Pulse" at the top of the page
GLOBAL_PULSE_SYMBOLS = ["^NSEI", "^GSPC", "^NDX", "^N225", "^STOXX50E", "^HSI"]


def get_all_assets():
    """Flatten everything into a single list - useful for testing/iterating all at once."""
    all_assets = []
    for region_assets in INDICES.values():
        all_assets.extend(region_assets)
    all_assets.extend(COMMODITIES)
    all_assets.extend(CURRENCIES)
    return all_assets