"""Economic news + symbol-specific news endpoints."""
from fastapi import APIRouter, HTTPException, Query

from app.data.news_feed import is_live_calendar_available, upcoming_events
from app.data.news_sentiment import aggregate_sentiment, fetch_symbol_news
from app.data.market_feed import SUPPORTED_SYMBOLS

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/upcoming")
def upcoming(hours: int = Query(48, ge=1, le=168), impact: str = Query("all")):
    items = upcoming_events(hours_ahead=hours)
    if impact != "all":
        items = [i for i in items if i.impact == impact.lower()]
    return {
        "source": "live" if is_live_calendar_available() else "synthetic",
        "count": len(items),
        "events": [
            {
                "title": i.title,
                "currency": i.currency,
                "impact": i.impact,
                "event_time": i.event_time.isoformat(),
                "forecast": i.forecast,
                "previous": i.previous,
                "actual": i.actual,
            }
            for i in items
        ],
    }


@router.get("/symbol/{symbol}")
def symbol_news(symbol: str, limit: int = Query(8, ge=1, le=25)):
    if symbol.upper() not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"unsupported symbol: {symbol}")
    items = fetch_symbol_news(symbol, limit=limit)
    agg = aggregate_sentiment(symbol)
    return {
        "symbol": symbol.upper(),
        "count": len(items),
        "headlines": items,
        "aggregate": agg,
    }
