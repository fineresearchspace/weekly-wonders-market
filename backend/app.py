"""
Weekly Wonders - Market Today Backend
Phase 4: Real API endpoints exposing market data over HTTP.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Allow imports from backend/data/ regardless of where uvicorn is run from
sys.path.append(os.path.join(os.path.dirname(__file__), "data"))

from market_config import INDICES, COMMODITIES, CURRENCIES, get_all_assets
from market_fetcher import get_market_data

app = FastAPI(title="Weekly Wonders Market API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this to your real domain before going live
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Weekly Wonders Market API is running"}


@app.get("/api/ping")
def ping():
    return {"status": "connected", "service": "market-today-backend"}


@app.get("/api/markets")
def get_all_markets():
    """
    Returns market data for every configured asset (all indices + commodities).
    Each asset's data is fetched independently - if one fails, the rest still
    return successfully (per the spec's error-handling requirement).
    """
    assets = get_all_assets()
    results = [get_market_data(asset) for asset in assets]
    return {
        "count": len(results),
        "available_count": sum(1 for r in results if r["available"]),
        "data": results,
    }


@app.get("/api/markets/region/{region}")
def get_markets_by_region(region: str):
    """
    Returns market data for one region: india, us, europe, asia, or commodities.
    Matches the regional tab navigation from the project spec.
    """
    region_map = {
        "india": INDICES.get("India", []),
        "us": INDICES.get("US", []),
        "europe": INDICES.get("Europe", []),
        "asia": INDICES.get("Asia", []),
        "commodities": COMMODITIES,
        "currencies": CURRENCIES,
    }

    assets = region_map.get(region.lower())

    if assets is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown region '{region}'. Valid options: {list(region_map.keys())}",
        )

    results = [get_market_data(asset) for asset in assets]
    return {
        "region": region,
        "count": len(results),
        "available_count": sum(1 for r in results if r["available"]),
        "data": results,
    }


@app.get("/api/history/{symbol}")
def get_history(symbol: str, period: str = "1mo"):
    """
    Returns historical price data for a single symbol, for charting later.
    Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y
    """
    import yfinance as yf

    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Valid options: {valid_periods}",
        )

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data available for symbol '{symbol}'",
            )

        history_points = [
            {"date": str(index.date()), "close": round(float(row["Close"]), 2)}
            for index, row in hist.iterrows()
            if not (row["Close"] != row["Close"])  # filters out NaN rows
        ]

        return {
            "symbol": symbol,
            "period": period,
            "points": history_points,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")