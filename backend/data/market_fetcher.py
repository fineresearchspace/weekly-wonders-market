"""
Weekly Wonders - Market Today
Phase 3: Fetch real market data and calculate price/change metrics.

For each asset, this returns latest price, previous close, absolute change,
and percentage change, or a clear "unavailable" result if the data is
missing or invalid (e.g. the KOSPI NaN case found in Phase 2).
"""

import math
from datetime import datetime, timezone
import yfinance as yf
from market_config import get_all_assets


def get_market_data(asset):
    """Fetch and calculate market data for a single asset."""
    base = {
        "name": asset["name"],
        "symbol": asset["symbol"],
        "region": asset["region"],
        "type": asset["type"],
        "latest_price": None,
        "previous_close": None,
        "change": None,
        "change_percent": None,
        "market_status": "unknown",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "available": False,
        "error": None,
    }

    try:
        ticker = yf.Ticker(asset["symbol"])
        hist = ticker.history(period="7d")

        if hist.empty:
            base["error"] = "No historical data returned"
            return base

        if len(hist) < 2:
            base["error"] = "Not enough history to calculate change (need at least 2 days)"
            return base

        latest_row = hist.iloc[-1]
        previous_row = hist.iloc[-2]

        latest_price = latest_row["Close"]
        previous_close = previous_row["Close"]

        if math.isnan(latest_price) or math.isnan(previous_close):
            base["error"] = "Data returned but price is NaN (invalid) - known yfinance gap for this symbol"
            return base

        change = latest_price - previous_close
        change_percent = (change / previous_close) * 100

        latest_date = hist.index[-1].date()
        today = datetime.now(timezone.utc).date()
        market_status = (
            "today's session (may be mid-day)" if latest_date == today
            else "closed - showing last available close"
        )

        base.update({
            "latest_price": round(float(latest_price), 2),
            "previous_close": round(float(previous_close), 2),
            "change": round(float(change), 2),
            "change_percent": round(float(change_percent), 2),
            "market_status": market_status,
            "available": True,
        })
        return base

    except Exception as e:
        base["error"] = f"Error fetching data: {str(e)}"
        return base


def main():
    """Test the fetcher against every configured asset and print results."""
    assets = get_all_assets()
    print(f"Fetching market data for {len(assets)} assets...\n")

    available_count = 0

    for asset in assets:
        data = get_market_data(asset)

        if data["available"]:
            available_count += 1
            direction = "UP" if data["change"] >= 0 else "DOWN"
            print(
                f"OK {data['name']:<25} | {data['latest_price']:>12} "
                f"| {direction} {data['change']:>8} ({data['change_percent']:>6}%) "
                f"| {data['market_status']}"
            )
        else:
            print(f"FAIL {data['name']:<25} | UNAVAILABLE - {data['error']}")

    print(f"\n{'='*70}")
    print(f"RESULTS: {available_count}/{len(assets)} assets returned usable data")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()