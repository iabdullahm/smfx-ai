"""Economic news feed — synthetic for MVP."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import Random
from typing import List

from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    currency: str
    impact: str       # low / medium / high
    event_time: datetime
    forecast: str = ""
    previous: str = ""
    actual: str = ""


_TEMPLATES = [
    ("CPI YoY", "USD", "high", "3.4%", "3.5%"),
    ("Core CPI MoM", "USD", "high", "0.3%", "0.4%"),
    ("Non-Farm Payrolls", "USD", "high", "175K", "187K"),
    ("Fed Interest Rate Decision", "USD", "high", "5.25%", "5.25%"),
    ("FOMC Statement", "USD", "high", "", ""),
    ("ECB Rate Decision", "EUR", "high", "4.00%", "4.00%"),
    ("GDP QoQ", "EUR", "medium", "0.3%", "0.2%"),
    ("BoJ Policy Statement", "JPY", "high", "", ""),
    ("UK CPI YoY", "GBP", "high", "2.3%", "2.4%"),
    ("Crude Oil Inventories", "USD", "medium", "-1.5M", "-3.2M"),
    ("Retail Sales MoM", "USD", "medium", "0.4%", "0.7%"),
    ("ISM Manufacturing PMI", "USD", "medium", "49.8", "49.2"),
    ("Unemployment Rate", "USD", "high", "3.8%", "3.9%"),
]


def upcoming_events(hours_ahead: int = 48, seed: int | None = None) -> List[NewsItem]:
    """Return a list of upcoming economic events ordered by time."""
    base = datetime.now(timezone.utc)
    bucket = int(base.timestamp() // 3600) if seed is None else seed
    rng = Random(bucket)
    items: list[NewsItem] = []
    count = rng.randint(6, 10)
    for _ in range(count):
        title, ccy, impact, forecast, previous = rng.choice(_TEMPLATES)
        offset = timedelta(hours=rng.uniform(0.5, max(1.0, float(hours_ahead))))
        items.append(NewsItem(
            title=title,
            currency=ccy,
            impact=impact,
            event_time=base + offset,
            forecast=forecast,
            previous=previous,
            actual="",
        ))
    items.sort(key=lambda x: x.event_time)
    return items


def minutes_until_next_high_impact(currency: str | None = None) -> float:
    """Return minutes until the next high-impact event (optionally filtered by currency).

    Returns +inf if no upcoming high-impact event in the window.
    """
    now = datetime.now(timezone.utc)
    for ev in upcoming_events(hours_ahead=48):
        if ev.impact != "high":
            continue
        if currency and ev.currency.upper() != currency.upper():
            continue
        return (ev.event_time - now).total_seconds() / 60.0
    return float("inf")
