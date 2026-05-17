"""Symbol-level news headlines + keyword-based sentiment scoring.

Source: Yahoo Finance via `yfinance` — gives recent news per ticker. We then
score each headline with a small bilingual (Arabic + English) keyword lexicon
to produce a sentiment in [-1, +1].

This isn't ML — it's a deliberately simple heuristic that's fast, free, and
catches the loudest signals. For higher accuracy we can swap in a small
fine-tuned model (e.g. FinBERT) later behind the same interface.
"""
from __future__ import annotations

import re
import time
from typing import Optional

# Reuse the symbol → yahoo ticker mapping
from app.data.yahoo_feed import SYMBOL_MAP


# Bilingual lexicons — weights are tuned so a few strong tokens move the score.
BULLISH_TERMS: dict[str, float] = {
    # English
    "rally": 0.6, "surge": 0.7, "soar": 0.8, "rebound": 0.5, "bullish": 0.7,
    "gains": 0.4, "rises": 0.4, "climb": 0.4, "advance": 0.3, "jumps": 0.5,
    "strong": 0.3, "outperform": 0.5, "upgrade": 0.6, "beat": 0.4,
    "demand": 0.3, "tightens": 0.3, "shortage": 0.4, "buy": 0.3,
    "all-time high": 0.7, "record high": 0.6, "breakout": 0.5,
    "safe haven": 0.4, "support": 0.2, "boost": 0.4, "boosts": 0.4,
    "rate cut": 0.5, "cuts": 0.3, "dovish": 0.5,
    # Arabic
    "ارتفاع": 0.5, "صعود": 0.6, "قفز": 0.6, "ربح": 0.4, "مكاسب": 0.5,
    "ارتداد": 0.4, "اختراق صاعد": 0.6, "صاعد": 0.5,
    "ملاذ آمن": 0.4, "خفض الفائدة": 0.5, "تيسير": 0.5,
}

BEARISH_TERMS: dict[str, float] = {
    # English
    "plunge": 0.8, "crash": 0.9, "tumble": 0.7, "slump": 0.7, "bearish": 0.7,
    "falls": 0.4, "drops": 0.4, "decline": 0.4, "retreat": 0.4, "slides": 0.5,
    "weak": 0.3, "underperform": 0.5, "downgrade": 0.6, "miss": 0.4,
    "supply glut": 0.5, "oversupply": 0.5, "sell": 0.3,
    "all-time low": 0.7, "record low": 0.6, "breakdown": 0.5,
    "rate hike": 0.5, "hike": 0.3, "hawkish": 0.5, "tightening": 0.4,
    "recession": 0.6, "crisis": 0.6, "fear": 0.4,
    # Arabic
    "هبوط": 0.5, "تراجع": 0.5, "خسائر": 0.5, "هابط": 0.5,
    "انهيار": 0.8, "ركود": 0.6, "أزمة": 0.6, "ضعف": 0.3,
    "رفع الفائدة": 0.5, "تشديد": 0.4,
}

_WORD_RE = re.compile(r"[\w؀-ۿ\-]+", re.UNICODE)


def _score_text(text: str) -> float:
    """Return sentiment in [-1, +1] for a headline/summary."""
    if not text:
        return 0.0
    lower = text.lower()
    score = 0.0
    # Multi-word terms first
    for term, w in BULLISH_TERMS.items():
        if term in lower:
            score += w
    for term, w in BEARISH_TERMS.items():
        if term in lower:
            score -= w
    # Squash to [-1, 1] via tanh
    import math
    return math.tanh(score)


# Simple TTL cache: yfinance news is rate-limited.
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL = 600   # 10 minutes


def fetch_symbol_news(symbol: str, limit: int = 8) -> list[dict]:
    """Return list of {title, publisher, link, published_at, sentiment} for the
    last few headlines. Empty list on any failure.
    """
    symbol = symbol.upper()
    if symbol not in SYMBOL_MAP:
        return []

    cached = _CACHE.get(symbol)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        return cached[1][:limit]

    try:
        import yfinance as yf
    except ImportError:
        return []

    ticker = SYMBOL_MAP[symbol]
    try:
        items = yf.Ticker(ticker).news or []
    except Exception:
        return []

    out: list[dict] = []
    for it in items[:20]:
        # yfinance has been changing news shape — handle both legacy and new
        content = it.get("content", it)
        title = content.get("title") or it.get("title") or ""
        summary = content.get("summary") or it.get("summary") or ""
        publisher = (content.get("provider") or {}).get("displayName") \
                    or it.get("publisher") or ""
        link = (content.get("clickThroughUrl") or {}).get("url") \
               or it.get("link") or ""
        pub = content.get("pubDate") or it.get("providerPublishTime") or 0
        if isinstance(pub, (int, float)) and pub > 0:
            try:
                from datetime import datetime, timezone
                pub_iso = datetime.fromtimestamp(int(pub), tz=timezone.utc).isoformat()
            except Exception:
                pub_iso = ""
        else:
            pub_iso = str(pub) if pub else ""
        sentiment = _score_text(f"{title}. {summary}")
        out.append({
            "title": title,
            "summary": summary[:280],
            "publisher": publisher,
            "link": link,
            "published_at": pub_iso,
            "sentiment": round(sentiment, 3),
        })

    _CACHE[symbol] = (time.time(), out)
    return out[:limit]


def aggregate_sentiment(symbol: str) -> Optional[dict]:
    """Aggregate the last few headlines into a single bias signal.

    Returns:
      {
        "score": float in [-1, +1],
        "n_articles": int,
        "bullish": int,
        "bearish": int,
        "neutral": int,
        "samples": [first 3 headlines]
      }
    Or None if no news available.
    """
    items = fetch_symbol_news(symbol, limit=12)
    if not items:
        return None
    scores = [it["sentiment"] for it in items]
    bullish = sum(1 for s in scores if s > 0.15)
    bearish = sum(1 for s in scores if s < -0.15)
    neutral = len(scores) - bullish - bearish
    # Weighted by recency: assume yfinance returns newest first.
    weights = [1.0 / (i + 1) for i in range(len(scores))]
    wsum = sum(weights)
    weighted = sum(s * w for s, w in zip(scores, weights)) / wsum
    return {
        "score": round(weighted, 3),
        "n_articles": len(items),
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "samples": [
            {"title": it["title"], "sentiment": it["sentiment"],
             "publisher": it["publisher"], "link": it["link"]}
            for it in items[:5]
        ],
    }
