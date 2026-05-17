"""Economic news feed — real ForexFactory calendar with synthetic fallback.

Source: nfs.faireconomy.media — public weekly JSON mirror of Forex Factory's
calendar (events: Fed, CPI, NFP, FOMC, BoJ, ECB, …).

If the live source is unreachable we fall back to a deterministic synthetic
calendar so the system keeps running offline / for tests.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from random import Random
from typing import List, Optional

import httpx
from pydantic import BaseModel


class NewsItem(BaseModel):
    title: str
    currency: str
    impact: str       # low / medium / high
    event_time: datetime
    forecast: str = ""
    previous: str = ""
    actual: str = ""


# --- Live source ---------------------------------------------------------

FOREXFACTORY_JSON = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
_LIVE_CACHE: dict[str, tuple[float, List[NewsItem]]] = {}
_LIVE_TTL = 1800   # 30 minutes


def _impact_from_ff(raw: str) -> str:
    raw = (raw or "").lower()
    if raw in ("high", "red"):
        return "high"
    if raw in ("medium", "orange", "yellow"):
        return "medium"
    return "low"


def _fetch_live() -> Optional[List[NewsItem]]:
    cached = _LIVE_CACHE.get("ff")
    if cached and time.time() - cached[0] < _LIVE_TTL:
        return cached[1]

    try:
        r = httpx.get(FOREXFACTORY_JSON, timeout=10, follow_redirects=True,
                      headers={"User-Agent": "SMFX-AI/1.0"})
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    items: List[NewsItem] = []
    for ev in data:
        try:
            # Forex Factory JSON shape: title, country, date, impact, forecast, previous, actual
            event_time = datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
            items.append(NewsItem(
                title=ev.get("title", ""),
                currency=(ev.get("country") or "").upper(),
                impact=_impact_from_ff(ev.get("impact", "")),
                event_time=event_time,
                forecast=str(ev.get("forecast", "") or ""),
                previous=str(ev.get("previous", "") or ""),
                actual=str(ev.get("actual", "") or ""),
            ))
        except Exception:
            continue

    items.sort(key=lambda x: x.event_time)
    _LIVE_CACHE["ff"] = (time.time(), items)
    return items


# --- Synthetic fallback --------------------------------------------------

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


def _synthetic(hours_ahead: int) -> List[NewsItem]:
    base = datetime.now(timezone.utc)
    bucket = int(base.timestamp() // 3600)
    rng = Random(bucket)
    items: list[NewsItem] = []
    count = rng.randint(6, 10)
    for _ in range(count):
        title, ccy, impact, forecast, previous = rng.choice(_TEMPLATES)
        offset = timedelta(hours=rng.uniform(0.5, max(1.0, float(hours_ahead))))
        items.append(NewsItem(
            title=title, currency=ccy, impact=impact,
            event_time=base + offset, forecast=forecast, previous=previous,
        ))
    items.sort(key=lambda x: x.event_time)
    return items


# --- Public API ----------------------------------------------------------

def upcoming_events(hours_ahead: int = 48, seed: int | None = None) -> List[NewsItem]:
    """Return events occurring within the next `hours_ahead` hours."""
    live = _fetch_live() if seed is None else None
    if live is not None:
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(hours=hours_ahead)
        return [ev for ev in live if now <= ev.event_time <= horizon]
    return _synthetic(hours_ahead)


def is_live_calendar_available() -> bool:
    return _fetch_live() is not None


def minutes_until_next_high_impact(currency: str | None = None) -> float:
    """Minutes until next high-impact event (optionally filtered by currency).
    Returns +inf if none is scheduled in the next 48h."""
    now = datetime.now(timezone.utc)
    for ev in upcoming_events(hours_ahead=48):
        if ev.impact != "high":
            continue
        if currency and ev.currency.upper() != currency.upper():
            continue
        return (ev.event_time - now).total_seconds() / 60.0
    return float("inf")
