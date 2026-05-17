"""Divergence detection — bullish / bearish / hidden divergences on RSI and MACD.

A divergence is one of the highest-conviction reversal/continuation patterns in
technical analysis. We scan the last ~50 bars for pivot pairs:

* **Bullish Regular**:  price makes Lower Low, oscillator makes Higher Low  → buy
* **Bearish Regular**:  price makes Higher High, oscillator makes Lower High → sell
* **Bullish Hidden** :  price makes Higher Low, oscillator makes Lower Low  → trend-continuation buy
* **Bearish Hidden** :  price makes Lower High, oscillator makes Higher High → trend-continuation sell
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.engines.base import EngineOutput


# --- indicators ----------------------------------------------------------

def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd_hist(close: pd.Series) -> pd.Series:
    e12 = close.ewm(span=12, adjust=False).mean()
    e26 = close.ewm(span=26, adjust=False).mean()
    macd = e12 - e26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal


def _find_pivots(values: np.ndarray, lookback: int = 3) -> tuple[list[int], list[int]]:
    """Return (high_indices, low_indices) — indices that are local extrema
    within ±lookback bars."""
    highs, lows = [], []
    n = len(values)
    for i in range(lookback, n - lookback):
        window = values[i - lookback:i + lookback + 1]
        if values[i] == np.nanmax(window):
            highs.append(i)
        if values[i] == np.nanmin(window):
            lows.append(i)
    return highs, lows


def _scan_divergence(price: pd.Series, osc: pd.Series, lookback: int = 3,
                     min_gap: int = 5) -> list[dict]:
    """Return divergence events found in the last ~40 bars."""
    p = price.values
    o = osc.values
    p_highs, p_lows = _find_pivots(p, lookback)
    o_highs, o_lows = _find_pivots(o, lookback)
    events: list[dict] = []
    horizon = max(0, len(price) - 50)

    # Pair the last two lows / highs
    def _pair_last_two(indices: list[int]) -> tuple[int, int] | None:
        idx = [i for i in indices if i >= horizon]
        if len(idx) < 2:
            return None
        a, b = idx[-2], idx[-1]
        if b - a < min_gap:
            return None
        return a, b

    pair = _pair_last_two(p_lows)
    if pair:
        a, b = pair
        # Match nearest oscillator low within ±2 bars
        o_lows_near_a = [i for i in o_lows if abs(i - a) <= 2]
        o_lows_near_b = [i for i in o_lows if abs(i - b) <= 2]
        if o_lows_near_a and o_lows_near_b:
            oa = o_lows_near_a[-1]; ob = o_lows_near_b[-1]
            # Bullish Regular: price LL, oscillator HL
            if p[b] < p[a] and o[ob] > o[oa]:
                events.append({"type": "bullish_regular", "price_idx": b, "osc_idx": ob})
            # Bullish Hidden: price HL, oscillator LL
            elif p[b] > p[a] and o[ob] < o[oa]:
                events.append({"type": "bullish_hidden", "price_idx": b, "osc_idx": ob})

    pair = _pair_last_two(p_highs)
    if pair:
        a, b = pair
        o_highs_near_a = [i for i in o_highs if abs(i - a) <= 2]
        o_highs_near_b = [i for i in o_highs if abs(i - b) <= 2]
        if o_highs_near_a and o_highs_near_b:
            oa = o_highs_near_a[-1]; ob = o_highs_near_b[-1]
            # Bearish Regular: price HH, oscillator LH
            if p[b] > p[a] and o[ob] < o[oa]:
                events.append({"type": "bearish_regular", "price_idx": b, "osc_idx": ob})
            # Bearish Hidden: price LH, oscillator HH
            elif p[b] < p[a] and o[ob] > o[oa]:
                events.append({"type": "bearish_hidden", "price_idx": b, "osc_idx": ob})

    return events


def analyze(df: pd.DataFrame) -> EngineOutput:
    out = EngineOutput(name="divergence")
    if len(df) < 50:
        out.notes.append("بيانات غير كافية لكشف Divergence")
        return out.clamp()

    close = df["close"]
    rsi = _rsi(close)
    macd_hist = _macd_hist(close)

    rsi_events = _scan_divergence(close, rsi)
    macd_events = _scan_divergence(close, macd_hist)

    all_events = [{"oscillator": "RSI", **e} for e in rsi_events] + \
                 [{"oscillator": "MACD", **e} for e in macd_events]

    score = 0.0
    labels_ar = {
        "bullish_regular":  "Divergence صعودي عادي — انعكاس صعودي محتمل",
        "bullish_hidden":   "Divergence صعودي مخفي — استمرار اتجاه صاعد",
        "bearish_regular":  "Divergence هبوطي عادي — انعكاس هبوطي محتمل",
        "bearish_hidden":   "Divergence هبوطي مخفي — استمرار اتجاه هابط",
    }
    direction_weight = {
        "bullish_regular":  +0.65,   # strong reversal
        "bullish_hidden":   +0.40,
        "bearish_regular":  -0.65,
        "bearish_hidden":   -0.40,
    }

    seen_types: set[str] = set()
    for ev in all_events:
        t = ev["type"]
        if t in seen_types:
            continue
        seen_types.add(t)
        score += direction_weight.get(t, 0.0)
        out.notes.append(f"{labels_ar[t]} على {ev['oscillator']}")
        out.signals.append({
            "oscillator": ev["oscillator"], "type": t,
            "price_idx": int(ev["price_idx"]), "osc_idx": int(ev["osc_idx"]),
        })

    if not all_events:
        out.notes.append("لا يوجد Divergence ظاهر حالياً")

    out.score = float(np.clip(score, -1.0, 1.0))
    out.confidence = 0.85 if all_events else 0.20
    return out.clamp()
