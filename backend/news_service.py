"""Curated market news: headline, short snapshot, image, source and original link."""
from __future__ import annotations
import hashlib, os, re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Iterable

import feedparser
import requests

# Only sources explicitly configured as approved feeds are fetched.
APPROVED_SOURCES = {
    "CNBC", "Reuters", "Bloomberg", "Financial Times", "The Wall Street Journal",
    "MarketWatch", "Yahoo Finance", "Barron's", "Mint", "Moneycontrol",
    "Economic Times Markets", "Business Standard", "Trading Economics",
    "RBI", "U.S. Federal Reserve", "SEBI", "NSE", "BSE"
}

# Feed URLs live in Render environment variables so individual feeds can be enabled/disabled
# without another code deploy. No paid API keys are required.
ENV_FEEDS = {
    "CNBC": "NEWS_RSS_CNBC",
    "Reuters": "NEWS_RSS_REUTERS",
    "Bloomberg": "NEWS_RSS_BLOOMBERG",
    "Financial Times": "NEWS_RSS_FINANCIAL_TIMES",
    "The Wall Street Journal": "NEWS_RSS_WSJ",
    "MarketWatch": "NEWS_RSS_MARKETWATCH",
    "Yahoo Finance": "NEWS_RSS_YAHOO_FINANCE",
    "Barron's": "NEWS_RSS_BARRONS",
    "Mint": "NEWS_RSS_MINT",
    "Moneycontrol": "NEWS_RSS_MONEYCONTROL",
    "Economic Times Markets": "NEWS_RSS_ECONOMIC_TIMES",
    "Business Standard": "NEWS_RSS_BUSINESS_STANDARD",
    "Trading Economics": "NEWS_RSS_TRADING_ECONOMICS",
    "RBI": "NEWS_RSS_RBI",
    "U.S. Federal Reserve": "NEWS_RSS_FED",
    "SEBI": "NEWS_RSS_SEBI",
    "NSE": "NEWS_RSS_NSE",
    "BSE": "NEWS_RSS_BSE",
}

FINANCE_TERMS = re.compile(
    r"\b(stock|share|market|invest|earnings|revenue|profit|ipo|merger|acquisition|bond|treasury|yield|interest rate|fed|federal reserve|rbi|inflation|gdp|jobs|employment|currency|rupee|dollar|forex|oil|gold|commodity|central bank|rate cut|rate hike|sensex|nifty|nasdaq|s&p|dow|debt|valuation|dividend|buyback|capex|economy)\b",
    re.I,
)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _parse_date(entry: Any) -> str:
    value = entry.get("published") or entry.get("updated") or entry.get("date")
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        return parsedate_to_datetime(str(value)).astimezone(timezone.utc).isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()


def _image(entry: Any) -> str | None:
    media = entry.get("media_content") or []
    if media and media[0].get("url"):
        return media[0]["url"]
    thumbs = entry.get("media_thumbnail") or []
    if thumbs and thumbs[0].get("url"):
        return thumbs[0]["url"]
    return entry.get("image") or entry.get("imageUrl") or None


def _snapshot(entry: Any) -> str:
    """Keep feed excerpts short; this app is a discovery layer, not an article mirror."""
    text = _clean(entry.get("summary") or entry.get("description") or "")
    if not text:
        return "Open the original source for the full story."
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:2])[:350]


def _category(text: str) -> str:
    text = text.lower()
    if any(x in text for x in ["earnings", "revenue", "profit", "ipo", "merger", "acquisition"]): return "Companies"
    if any(x in text for x in ["bond", "treasury", "yield", "interest rate", "fed", "rbi", "central bank"]): return "Rates & Bonds"
    if any(x in text for x in ["inflation", "gdp", "employment", "jobs", "economic"]): return "Macro"
    if any(x in text for x in ["oil", "gold", "commodity"]): return "Commodities"
    if any(x in text for x in ["currency", "rupee", "dollar", "forex"]): return "FX"
    return "Markets"


def _normalize(source: str, entry: Any) -> dict[str, Any] | None:
    headline = _clean(entry.get("title") or "")
    url = entry.get("link") or entry.get("url") or ""
    snapshot = _snapshot(entry)
    if not headline or not url:
        return None
    combined = f"{headline} {snapshot}"
    if not FINANCE_TERMS.search(combined):
        return None
    return {
        "id": hashlib.sha256((source + url).encode()).hexdigest()[:20],
        "source": source,
        "sourceUrl": url,
        "headline": headline,
        "snapshot": snapshot,
        "imageUrl": _image(entry),
        "publishedAt": _parse_date(entry),
        "category": _category(combined),
    }


def _fetch_feed(source: str, url: str) -> list[dict[str, Any]]:
    try:
        response = requests.get(url, timeout=12, headers={"User-Agent": "WeeklyWondersMarket/1.0"})
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        return [story for entry in parsed.entries if (story := _normalize(source, entry))]
    except Exception:
        return []


def _deduplicate(stories: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen, output = set(), []
    for story in stories:
        key = " ".join(re.sub(r"[^a-z0-9 ]", "", story["headline"].lower()).split()[:12])
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(story)
    return output


def get_curated_news(source: str | None = None, category: str | None = None, limit: int = 40) -> dict[str, Any]:
    selected = [source] if source else list(ENV_FEEDS.keys())
    stories, unavailable, configured = [], [], []

    for provider in selected:
        if provider not in APPROVED_SOURCES:
            continue
        env_name = ENV_FEEDS.get(provider)
        url = os.getenv(env_name, "") if env_name else ""
        if not url:
            unavailable.append(provider)
            continue
        configured.append(provider)
        stories.extend(_fetch_feed(provider, url))

    stories = _deduplicate(stories)
    if category:
        stories = [story for story in stories if story["category"].lower() == category.lower()]
    stories.sort(key=lambda story: story["publishedAt"], reverse=True)
    stories = stories[:max(1, min(limit, 100))]

    return {
        "count": len(stories),
        "data": stories,
        "configuredSources": configured,
        "unavailableSources": unavailable,
        "approvedSources": sorted(APPROVED_SOURCES),
    }
