"""
Weekly Wonders - Market Today
Phase 2: Verify which configured symbols actually return data from yfinance.

Run this BEFORE building any fetching/API logic on top of market_config.py.
Symbols that fail here need a replacement ticker or should be dropped.
"""

import math
import yfinance as yf
from market_config import get_all_assets

def test_symbol(asset):
    """Try to pull 5 days of history for one asset. Return True/False + a reason."""
    try:
        ticker = yf.Ticker(asset["symbol"])
        hist = ticker.history(period="5d")

        if hist.empty:
            return False, "No data returned (empty history)"

        latest_close = hist["Close"].iloc[-1]

        # A row can come back with a NaN close price — this is NOT valid data,
        # even though the history call technically "succeeded."
        if math.isnan(latest_close):
            return False, "Data returned but close price is NaN (invalid)"

        return True, f"Latest close: {latest_close:.2f}"

    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    assets = get_all_assets()
    working = []
    broken = []

    print(f"Testing {len(assets)} symbols...\n")

    for asset in assets:
        success, detail = test_symbol(asset)
        status = "✅ OK  " if success else "❌ FAIL"
        print(f"{status} | {asset['name']:<25} ({asset['symbol']:<12}) | {detail}")

        if success:
            working.append(asset)
        else:
            broken.append(asset)

    print(f"\n{'='*60}")
    print(f"RESULTS: {len(working)}/{len(assets)} symbols working")
    print(f"{'='*60}")

    if broken:
        print("\nSymbols that need attention:")
        for asset in broken:
            print(f"  - {asset['name']} ({asset['symbol']}) — {asset['region']}")


if __name__ == "__main__":
    main()