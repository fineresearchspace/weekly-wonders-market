"""Curated finance news service using approved feeds and optional news APIs."""
from __future__ import annotations
import hashlib, os, re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Iterable
import feedparser, requests

APPROVED_SOURCES={"Reuters","Bloomberg","Financial Times","The Wall Street Journal","CNBC","Trading Economics","MarketWatch","Yahoo Finance","Barron's","Mint","Moneycontrol","Economic Times Markets","Business Standard","RBI","U.S. Federal Reserve","SEBI","NSE","BSE","Finnhub","Alpha Vantage","NewsAPI"}
ENV_FEEDS={"CNBC":"NEWS_RSS_CNBC","Reuters":"NEWS_RSS_REUTERS","Financial Times":"NEWS_RSS_FINANCIAL_TIMES","MarketWatch":"NEWS_RSS_MARKETWATCH","Yahoo Finance":"NEWS_RSS_YAHOO_FINANCE","Mint":"NEWS_RSS_MINT","Moneycontrol":"NEWS_RSS_MONEYCONTROL","Economic Times Markets":"NEWS_RSS_ECONOMIC_TIMES","Business Standard":"NEWS_RSS_BUSINESS_STANDARD"}
FINANCE_TERMS=re.compile(r"\b(stock|stocks|share|shares|market|markets|invest|investing|earnings|revenue|profit|ipo|merger|acquisition|m&a|bond|bonds|treasury|yield|yields|interest rate|fed|federal reserve|rbi|inflation|gdp|jobs|employment|unemployment|currency|rupee|dollar|forex|oil|gold|commodity|commodities|central bank|rate cut|rate hike|sensex|nifty|nasdaq|s&p|dow|credit|debt|valuation|dividend|buyback|capital expenditure|capex|ai spending)\b",re.I)
API_PROVIDERS=("Trading Economics","Finnhub","Alpha Vantage","NewsAPI")

def _parse_date(entry:Any)->str:
    value=entry.get("published") or entry.get("updated") or entry.get("date") or entry.get("time_published") or entry.get("datetime")
    if isinstance(value,(int,float)): return datetime.fromtimestamp(value,tz=timezone.utc).isoformat()
    if not value:return datetime.now(timezone.utc).isoformat()
    try:return parsedate_to_datetime(str(value)).astimezone(timezone.utc).isoformat()
    except Exception:
        try:return datetime.strptime(str(value),"%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).isoformat()
        except Exception:
            try:return datetime.fromisoformat(str(value).replace("Z","+00:00")).astimezone(timezone.utc).isoformat()
            except Exception:return datetime.now(timezone.utc).isoformat()

def _image(entry:Any)->str|None:
    media=entry.get("media_content") or []
    if media and media[0].get("url"):return media[0]["url"]
    thumbs=entry.get("media_thumbnail") or []
    if thumbs and thumbs[0].get("url"):return thumbs[0]["url"]
    return entry.get("image") or entry.get("imageUrl") or entry.get("banner_image") or None

def _clean_summary(text:str)->str:return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",text or "")).strip()
def _snapshot(entry:Any)->str:
    text=_clean_summary(entry.get("summary") or entry.get("description") or "")
    if not text:return "Open the original report for the full market update."
    return " ".join(re.split(r"(?<=[.!?])\s+",text)[:3])[:900]
def _category(text:str)->str:
    text=text.lower()
    if any(x in text for x in ["earnings","revenue","profit","ipo","merger","acquisition"]):return "Companies"
    if any(x in text for x in ["bond","treasury","yield","interest rate","fed","rbi","central bank"]):return "Rates & Bonds"
    if any(x in text for x in ["inflation","gdp","employment","jobs","economic"]):return "Macro"
    if any(x in text for x in ["oil","gold","commodity","commodities"]):return "Commodities"
    if any(x in text for x in ["currency","rupee","dollar","forex"]):return "FX"
    return "Markets"
def _normalize(source:str,entry:Any)->dict[str,Any]|None:
    headline=_clean_summary(entry.get("title") or entry.get("headline") or "")
    url=entry.get("link") or entry.get("url") or ""
    snapshot=_snapshot(entry)
    if not headline or not url:return None
    combined=f"{headline} {snapshot}"
    if not FINANCE_TERMS.search(combined):return None
    actual_source=_clean_summary(entry.get("source") or source)
    return {"id":hashlib.sha256((actual_source+url).encode()).hexdigest()[:20],"source":actual_source,"sourceUrl":url,"headline":headline,"snapshot":snapshot,"imageUrl":_image(entry),"publishedAt":_parse_date(entry),"category":_category(combined)}
def _fetch_feed(source:str,url:str)->list[dict[str,Any]]:
    try:
        r=requests.get(url,timeout=10,headers={"User-Agent":"WeeklyWondersMarket/1.0"});r.raise_for_status();p=feedparser.parse(r.content)
        return [s for e in p.entries if (s:=_normalize(source,e))]
    except Exception:return []
def _fetch_trading_economics()->list[dict[str,Any]]:
    key=os.getenv("TRADING_ECONOMICS_API_KEY",""); stories=[]
    if not key:return stories
    for news_type in ("markets","economy"):
        try:
            r=requests.get("https://api.tradingeconomics.com/news",params={"type":news_type,"c":key,"f":"json"},timeout=10);r.raise_for_status()
            stories.extend(s for item in r.json() if (s:=_normalize("Trading Economics",item)))
        except Exception:continue
    return stories
def _fetch_finnhub()->list[dict[str,Any]]:
    key=os.getenv("FINNHUB_API_KEY","")
    if not key:return []
    try:
        r=requests.get("https://finnhub.io/api/v1/news",params={"category":"general","token":key},timeout=10);r.raise_for_status()
        return [s for item in r.json() if (s:=_normalize("Finnhub",item))]
    except Exception:return []
def _fetch_alpha_vantage()->list[dict[str,Any]]:
    key=os.getenv("ALPHA_VANTAGE_API_KEY","")
    if not key:return []
    try:
        r=requests.get("https://www.alphavantage.co/query",params={"function":"NEWS_SENTIMENT","topics":"financial_markets,economy_macro,economy_monetary,finance","sort":"LATEST","limit":50,"apikey":key},timeout=15);r.raise_for_status();data=r.json()
        return [s for item in data.get("feed",[]) if (s:=_normalize("Alpha Vantage",item))]
    except Exception:return []
def _fetch_newsapi()->list[dict[str,Any]]:
    key=os.getenv("NEWSAPI_KEY","")
    if not key:return []
    try:
        domains="reuters.com,cnbc.com,bloomberg.com,ft.com,livemint.com,moneycontrol.com,marketwatch.com"
        r=requests.get("https://newsapi.org/v2/everything",params={"q":"markets OR stocks OR investing OR economy OR bonds","domains":domains,"language":"en","sortBy":"publishedAt","pageSize":50,"apiKey":key},timeout=15);r.raise_for_status();data=r.json()
        return [s for item in data.get("articles",[]) if (s:=_normalize("NewsAPI",item))]
    except Exception:return []
def _deduplicate(stories:Iterable[dict[str,Any]])->list[dict[str,Any]]:
    seen=set();out=[]
    for s in stories:
        key=" ".join(re.sub(r"[^a-z0-9 ]","",s["headline"].lower()).split()[:12])
        if key and key in seen:continue
        seen.add(key);out.append(s)
    return out
def get_curated_news(source:str|None=None,category:str|None=None,limit:int=40)->dict[str,Any]:
    selected=[source] if source else list(ENV_FEEDS.keys())+list(API_PROVIDERS)
    stories=[];unavailable=[];configured=[]
    for provider in selected:
        if provider not in APPROVED_SOURCES:continue
        if provider=="Trading Economics":
            if not os.getenv("TRADING_ECONOMICS_API_KEY"):unavailable.append(provider)
            else:configured.append(provider);stories.extend(_fetch_trading_economics())
        elif provider=="Finnhub":
            if not os.getenv("FINNHUB_API_KEY"):unavailable.append(provider)
            else:configured.append(provider);stories.extend(_fetch_finnhub())
        elif provider=="Alpha Vantage":
            if not os.getenv("ALPHA_VANTAGE_API_KEY"):unavailable.append(provider)
            else:configured.append(provider);stories.extend(_fetch_alpha_vantage())
        elif provider=="NewsAPI":
            if not os.getenv("NEWSAPI_KEY"):unavailable.append(provider)
            else:configured.append(provider);stories.extend(_fetch_newsapi())
        else:
            env=ENV_FEEDS.get(provider);url=os.getenv(env,"") if env else ""
            if not url:unavailable.append(provider)
            else:configured.append(provider);stories.extend(_fetch_feed(provider,url))
    stories=_deduplicate(stories)
    if category:stories=[s for s in stories if s["category"].lower()==category.lower()]
    stories.sort(key=lambda x:x["publishedAt"],reverse=True)
    stories=stories[:max(1,min(limit,100))]
    return {"count":len(stories),"data":stories,"configuredSources":configured,"unavailableSources":unavailable,"approvedSources":sorted(APPROVED_SOURCES)}