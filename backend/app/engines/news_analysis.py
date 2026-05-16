"""News & events analysis — score is mostly a *risk* factor that lowers
confidence around high-impact events; mild directional bias on currency."""
from __future__ import annotations

import pandas as pd

from app.data.news_feed import minutes_until_next_high_impact
from app.engines.base import EngineOutput


# Which "currency" mostly drives each instrument's news exposure.
_SYMBOL_CCY = {
    "XAUUSD": "USD",
    "XAGUSD": "USD",
    "WTIUSD": "USD",
    "EURUSD": "USD",
    "GBPUSD": "USD",
    "USDJPY": "USD",
    "AUDUSD": "USD",
    "USDCAD": "USD",
    "BTCUSD": "USD",
}


def analyze(df: pd.DataFrame, symbol: str = "") -> EngineOutput:
    out = EngineOutput(name="news_analysis")
    ccy = _SYMBOL_CCY.get(symbol.upper(), "USD")
    mins = minutes_until_next_high_impact(currency=ccy)

    if mins < 60:
        out.score = 0.0
        out.confidence = 0.1
        out.notes.append(f"⚠ خبر عالي التأثير خلال {mins:.0f} دقيقة — يُفضل تجنب الدخول")
    elif mins < 240:
        out.score = 0.0
        out.confidence = 0.3
        out.notes.append(f"حدث {ccy} مهم خلال {mins / 60:.1f} ساعة — حذر")
    elif mins == float("inf"):
        out.score = 0.0
        out.confidence = 0.5
        out.notes.append("لا أحداث عالية التأثير في الأفق القريب")
    else:
        out.score = 0.0
        out.confidence = 0.6
        out.notes.append(f"الحدث القادم بعيد ({mins / 60:.1f} ساعة) — ظروف هادئة")

    out.signals.append({"minutes_to_next_high_impact": (None if mins == float("inf") else round(mins, 1)),
                        "currency": ccy})
    return out.clamp()
