"""
Weekly Wonders - Market Today Backend
Market data plus curated finance news and newsletter generation endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "data"))

from market_config import INDICES, COMMODITIES, CURRENCIES, get_all_assets
from market_fetcher import get_market_data
from backend.news_service import get_curated_news
from backend.newsletter_service import generate_newsletter

app = FastAPI(title="Weekly Wonders Market API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewsStory(BaseModel):
    id: str | None = None
    source: str
    sourceUrl: str
    headline: str
    snapshot: str
    imageUrl: str | None = None
    publishedAt: str | None = None
    category: str | None = None


class NewsletterRequest(BaseModel):
    stories: list[NewsStory] = Field(min_length=1, max_length=30)
    title: str = "Daily Wonder"


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Weekly Wonders Market API is running"}


@app.get("/api/ping")
def ping():
    return {"status": "connected", "service": "market-today-backend"}


@app.get("/api/markets")
def get_all_markets():
    assets = get_all_assets()
    results = [get_market_data(asset) for asset in assets]
    return {
        "count": len(results),
        "available_count": sum(1 for r in results if r["available"]),
        "data": results,
    }


@app.get("/api/markets/region/{region}")
def get_markets_by_region(region: str):
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
        raise HTTPException(status_code=404, detail=f"Unknown region '{region}'. Valid options: {list(region_map.keys())}")
    results = [get_market_data(asset) for asset in assets]
    return {"region": region, "count": len(results), "available_count": sum(1 for r in results if r["available"]), "data": results}


@app.get("/api/history/{symbol}")
def get_history(symbol: str, period: str = "1mo"):
    import yfinance as yf
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y"]
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period '{period}'. Valid options: {valid_periods}")
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data available for symbol '{symbol}'")
        history_points = [{"date": str(index.date()), "close": round(float(row["Close"]), 2)} for index, row in hist.iterrows() if not (row["Close"] != row["Close"])]
        return {"symbol": symbol, "period": period, "points": history_points}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@app.get("/api/news")
def get_news(source: str | None = None, category: str | None = None, limit: int = 40):
    """Return finance-only news from configured approved-source feeds."""
    return get_curated_news(source=source, category=category, limit=limit)


@app.get("/api/news/sources")
def get_news_sources():
    return get_curated_news(limit=1)


@app.post("/api/newsletter/generate")
def create_newsletter(request: NewsletterRequest):
    """Create a reviewable newsletter draft from explicitly selected stories."""
    return generate_newsletter([story.model_dump() for story in request.stories], request.title)
