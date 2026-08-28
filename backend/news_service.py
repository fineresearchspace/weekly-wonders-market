"""Curated finance news service.

The service normalizes approved-source feeds, filters for finance relevance,
and exposes a small provider abstraction. Providers can be implemented with
official APIs, RSS feeds, or other permitted access methods without changing
the API or frontend.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Iterable

import feedparser
import requests

APPROVED_SOURCES = {
    "Reuters", "Bloomberg", "Financial Times", "The Wall Street Journal", "CNBC",
    "Trading Economics", "MarketWatch", "Yahoo Finance", "Barron's",
    "Mint", "Moneycontrol", "Economic Times Markets", "Business Standard",
    "RBI", "U.S. Federal Reserve", "SEBI", "NSE", "BSE",
}

# RSS feeds are configured through environment variables so URLs can be changed
# without code changes. Only feeds belonging to approved publishers are accepted.
ENV_FEEDS = {
    "CNBC": "NEWS_RSS_CNBC",
    "Reuters": "NEWS_RSS_REUTERS",
    "Financial Times": "NEWS_RSS_FINANCIAL_TIMES",
    "MarketWatch": "NEWS_RSS_MARKETWATCH",
    "Yahoo Finance": "NEWS_RSS_YAHOO_FINANCE",
    "Mint": "NEWS_RSS_MINT",
    "Moneycontrol": "NEWS_RSS_MONEYCONTROL",
    "Economic Times Markets": "NEWS_RSS_ECONOMIC_TIMES",
    "Business Standard": "NEWS_RSS_BUSINESS_STANDARD",
    "Trading Economics": "NEWS_RSS_TRADING_ECONOMICS",
}

FINANCE_TERMS = re.compile(
    r"\b(stock|stocks|share|shares|market|markets|invest|investing|earnings|revenue|profit|"
    r"ipo|merger|acquisition|m&a|bond|bonds|treasury|yield|yields|interest rate|fed|federal reserve|"
    r"rbi|inflation|gdp|jobs|employment|unemployment|currency|rupee|dollar|forex|oil|gold|commodity|"
    r"commodities|central bank|rate cut|rate hike|sensex|nifty|nasdaq|s&p|dow|credit|debt|valuation|"
    r"dividend|buyback|capital expenditure|capex|ai spending)\b",
    re.IGNORECASE,
)


def _parse_date(entry: Any) -> str:
    value = entry.get("published") or entry.get("updated")
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _image(entry: Any) -> str | None:
    media = entry.get("media_content") or []
    if media and media[0].get("url"):
        return media[0]["url"]
    thumbs = entry.get("media_thumbnail") or []
    if thumbs and thumbs[0].get("url"):
        return thumbs[0]["url"]
    return None


def _clean_summary(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _snapshot(entry: Any) -> str:
    # Use only feed-provided metadata. This deliberately avoids fabricating facts.
    text = _clean_summary(entry.get("summary") or entry.get("description") or "")
    if not text:
        return "Open the original report for the full market update."
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:3])[:900]


def _category(text: str) -> str:
    text = text.lower()
    if any(x in text for x in ["earnings", "revenue", "profit", "ipo", "merger", "acquisition"]):
        return "Companies"
    if any(x in text for x in ["bond", "treasury", "yield", "interest rate", "fed", "rbi", "central bank"]):
        return "Rates & Bonds"
    if any(x in text for x in ["inflation", "gdp", "employment", "jobs", "economic"]):
        return "Macro"
    if any(x in text for x in ["oil", "gold", "commodity", "commodities"]):
        return "Commodities"
    if any(x in text for x in ["currency", "rupee", "dollar", "forex"]):
        return "FX"
    return "Markets"


def _normalize(source: str, entry: Any) -> dict[str, Any] | None:
    headline = _clean_summary(entry.get("title") or "")
    url = entry.get("link") or ""
    snapshot = _snapshot(entry)
    if not headline or not url:
        return None
    combined = f"{headline} {snapshot}"
    if not FINANCE_TERMS.search(combined):
        return None
    story_id = hashlib.sha256((source + url).encode()).hexdigest()[:20]
    return {
        "id": story_id,
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
        response = requests.get(url, timeout=10, headers={"User-Agent": "WeeklyWondersMarket/1.0"})
        response.raise_for_status()
        parsed = feedparser.parse(response.content)
        return [story for entry in parsed.entries if (story := _normalize(source, entry))]
    except Exception:
        return []


def _deduplicate(stories: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output = []
    for story in stories:
        key = re.sub(r"[^a-z0-9 ]", "", story["headline"].lower())
        key = " ".join(key.split()[:12])
        if key and key in seen:
            continue
        seen.add(key)
        output.append(story)
    return output


def get_curated_news(source: str | None = None, category: str | None = None, limit: int = 40) -> dict[str, Any]:
    selected = [source] if source else list(ENV_FEEDS.keys())
    stories: list[dict[str, Any]] = []
    unavailable: list[str] = []

    for provider in selected:
        if provider not in APPROVED_SOURCES:
            continue
        env_name = ENV_FEEDS.get(provider)
        feed_url = os.getenv(env_name, "") if env_name else ""
        if not feed_url:
            unavailable.append(provider)
            continue
        stories.extend(_fetch_feed(provider, feed_url))

    stories = _deduplicate(stories)
    if category:
        stories = [story for story in stories if story["category"].lower() == category.lower()]
    stories.sort(key=lambda item: item["publishedAt"], reverse=True)
    stories = stories[:max(1, min(limit, 100))]

    return {
        "count": len(stories),
        "data": stories,
        "configuredSources": [s for s in selected if s not in unavailable],
        "unavailableSources": unavailable,
        "approvedSources": sorted(APPROVED_SOURCES),
    }
