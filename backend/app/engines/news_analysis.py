"""News & events analysis.

Combines two real signals:
1. **Risk filter** — lowers confidence around high-impact economic events
   (Fed, CPI, NFP, FOMC, …). When an event is within 60 min we essentially
   suspend directional bias.
2. **Sentiment bias** — uses Yahoo headlines + bilingual keyword sentiment to
   nudge the score bullish/bearish based on recent news for the symbol.
"""
from __future__ import annotations

import pandas as pd

from app.data.news_feed import minutes_until_next_high_impact
from app.data.news_sentiment import aggregate_sentiment
from app.engines.base import EngineOutput


_SYMBOL_CCY = {
    "XAUUSD": "USD", "XAGUSD": "USD", "WTIUSD": "USD",
    "EURUSD": "USD", "GBPUSD": "USD", "USDJPY": "USD",
    "AUDUSD": "USD", "USDCAD": "USD", "BTCUSD": "USD",
}


def analyze(df: pd.DataFrame, symbol: str = "") -> EngineOutput:
    out = EngineOutput(name="news_analysis")
    symbol = symbol.upper()
    ccy = _SYMBOL_CCY.get(symbol, "USD")

    # --- Risk window around high-impact macro events ---
    mins = minutes_until_next_high_impact(currency=ccy)
    if mins < 60:
        out.score = 0.0
        out.confidence = 0.10
        out.notes.append(f"⚠ خبر عالي التأثير خلال {mins:.0f} دقيقة — يُفضل تجنب الدخول")
        out.signals.append({"event_window_minutes": round(mins, 1), "currency": ccy})
        return out.clamp()

    if mins < 240:
        out.notes.append(f"حدث {ccy} مهم خلال {mins / 60:.1f} ساعة — حذر")
        base_conf = 0.30
    elif mins == float("inf"):
        out.notes.append("لا أحداث عالية التأثير في الأفق القريب")
        base_conf = 0.55
    else:
        out.notes.append(f"الحدث القادم بعيد ({mins / 60:.1f} ساعة) — ظروف هادئة")
        base_conf = 0.60

    out.signals.append({
        "minutes_to_next_high_impact": (None if mins == float("inf") else round(mins, 1)),
        "currency": ccy,
    })

    # --- Sentiment bias from symbol-specific headlines ---
    try:
        senti = aggregate_sentiment(symbol)
    except Exception:
        senti = None

    if senti and senti["n_articles"] > 0:
        s = senti["score"]
        out.score = float(s)
        # Confidence scales with article count + absolute sentiment
        sentiment_conf = min(0.95, 0.40 + 0.04 * senti["n_articles"] + 0.4 * abs(s))
        out.confidence = max(base_conf, sentiment_conf)
        label = "إيجابية" if s > 0.15 else "سلبية" if s < -0.15 else "محايدة"
        out.notes.append(
            f"مشاعر الأخبار {label} ({s:+.2f}) "
            f"— {senti['bullish']} صعودية، {senti['bearish']} هبوطية، "
            f"{senti['neutral']} محايدة من {senti['n_articles']} مقالة"
        )
        out.signals.append({
            "sentiment_score": s,
            "bullish_headlines": senti["bullish"],
            "bearish_headlines": senti["bearish"],
            "neutral_headlines": senti["neutral"],
            "n_articles": senti["n_articles"],
            "samples": senti["samples"],
        })
    else:
        out.score = 0.0
        out.confidence = base_conf
        out.notes.append("لا توجد عناوين أخبار حديثة للرمز")

    return out.clamp()
