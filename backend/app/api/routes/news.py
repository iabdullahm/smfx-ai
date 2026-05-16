"""Economic news feed routes."""
from fastapi import APIRouter, Query

from app.data.news_feed import upcoming_events

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/upcoming")
def upcoming(hours: int = Query(48, ge=1, le=168), impact: str = Query("all")):
    items = upcoming_events(hours_ahead=hours)
    if impact != "all":
        items = [i for i in items if i.impact == impact.lower()]
    return [
        {
            "title": i.title,
            "currency": i.currency,
            "impact": i.impact,
            "event_time": i.event_time.isoformat(),
            "forecast": i.forecast,
            "previous": i.previous,
        }
        for i in items
    ]
