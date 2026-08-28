# Weekly Wonders Market

## Curated Market News

The feature branch `feature/curated-market-news` adds:

- `GET /api/news` for normalized, finance-only stories.
- `GET /api/news/sources` for approved/configured sources.
- `POST /api/newsletter/generate` for newsletter drafts from selected stories.
- `frontend/index.html` as a lightweight browser UI for browsing, selecting, and drafting.

### Feed configuration

Configure only approved publisher feeds with environment variables. The backend currently supports:

- `NEWS_RSS_CNBC`
- `NEWS_RSS_REUTERS`
- `NEWS_RSS_FINANCIAL_TIMES`
- `NEWS_RSS_MARKETWATCH`
- `NEWS_RSS_YAHOO_FINANCE`
- `NEWS_RSS_MINT`
- `NEWS_RSS_MONEYCONTROL`
- `NEWS_RSS_ECONOMIC_TIMES`
- `NEWS_RSS_BUSINESS_STANDARD`
- `NEWS_RSS_TRADING_ECONOMICS`

The service intentionally does not substitute unapproved sources when a configured source is unavailable.

Serve the FastAPI application as usual, then host `frontend/index.html` from the same origin or configure your web server to proxy `/api` requests to the backend.
