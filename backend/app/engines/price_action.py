"""Price action: candlestick patterns + S/R + BOS / CHoCH."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.engines.base import EngineOutput


def _swing_points(df: pd.DataFrame, lookback: int = 3) -> tuple[list[int], list[int]]:
    highs, lows = [], []
    h, l = df["high"].values, df["low"].values
    for i in range(lookback, len(df) - lookback):
        if h[i] == max(h[i - lookback:i + lookback + 1]):
            highs.append(i)
        if l[i] == min(l[i - lookback:i + lookback + 1]):
            lows.append(i)
    return highs, lows


def _last_candle_pattern(df: pd.DataFrame) -> str | None:
    if len(df) < 3:
        return None
    o = df["open"].iloc[-1]; c = df["close"].iloc[-1]
    h = df["high"].iloc[-1]; l = df["low"].iloc[-1]
    body = abs(c - o)
    range_ = max(h - l, 1e-9)

    # Pin bar / Hammer / Shooting star
    upper = h - max(o, c)
    lower = min(o, c) - l
    if body / range_ < 0.35 and lower > 2 * body and upper < body:
        return "Hammer / Bullish Pin"
    if body / range_ < 0.35 and upper > 2 * body and lower < body:
        return "Shooting Star / Bearish Pin"

    # Engulfing
    op = df["open"].iloc[-2]; cp = df["close"].iloc[-2]
    if c > o and op > cp and c >= op and o <= cp:
        return "Bullish Engulfing"
    if c < o and op < cp and c <= op and o >= cp:
        return "Bearish Engulfing"

    return None


def analyze(df: pd.DataFrame) -> EngineOutput:
    out = EngineOutput(name="price_action")
    if len(df) < 30:
        out.notes.append("بيانات غير كافية لتحليل حركة السعر")
        return out.clamp()

    score = 0.0
    highs_idx, lows_idx = _swing_points(df, lookback=3)
    last_close = df["close"].iloc[-1]

    # Recent S/R
    recent_high = df["high"].iloc[-30:].max()
    recent_low = df["low"].iloc[-30:].min()
    pos = (last_close - recent_low) / max(recent_high - recent_low, 1e-9)

    if pos < 0.25:
        score += 0.4
        out.notes.append(f"السعر قرب الدعم الحديث ({recent_low:.4f})")
    elif pos > 0.75:
        score -= 0.4
        out.notes.append(f"السعر قرب المقاومة الحديثة ({recent_high:.4f})")

    # Structure: HH/HL vs LH/LL
    if len(highs_idx) >= 2 and len(lows_idx) >= 2:
        h_now, h_prev = df["high"].iloc[highs_idx[-1]], df["high"].iloc[highs_idx[-2]]
        l_now, l_prev = df["low"].iloc[lows_idx[-1]], df["low"].iloc[lows_idx[-2]]
        if h_now > h_prev and l_now > l_prev:
            score += 0.3
            out.notes.append("هيكل صاعد (HH/HL)")
        elif h_now < h_prev and l_now < l_prev:
            score -= 0.3
            out.notes.append("هيكل هابط (LH/LL)")

    # Candle pattern bias
    pat = _last_candle_pattern(df)
    if pat:
        if "Bullish" in pat or "Hammer" in pat:
            score += 0.3
        elif "Bearish" in pat or "Shooting" in pat:
            score -= 0.3
        out.notes.append(f"نمط شمعة: {pat}")
        out.signals.append({"pattern": pat})

    out.signals.append({
        "support": round(float(recent_low), 4),
        "resistance": round(float(recent_high), 4),
        "position_pct": round(float(pos * 100), 1),
    })

    out.score = float(np.clip(score, -1.0, 1.0))
    out.confidence = min(1.0, 0.45 + abs(out.score) * 0.5)
    return out.clamp()
