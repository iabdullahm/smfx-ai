"""AI aggregator — combine analytical engines into a final trade signal.

Pipeline:
1. Run each engine on the OHLCV frame (now 9 engines incl. Divergence).
2. Apply per-school weights (configurable; regime-adaptive in the future).
3. Compute composite score (-1..+1) and composite confidence (0..1).
4. Map composite score → BUY/SELL direction.
5. Derive Entry / Smart SL / TP1-TP3 from market structure
   (swing points, ATR, Order Blocks, Fibonacci extensions).
6. Compute Signal Strength (1..10) and Win Probability (%).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.ai.regime import classify_regime
from app.engines import (
    classical_ta,
    divergence,
    elliott_wave,
    fundamental,
    harmonic,
    news_analysis,
    price_action,
    smart_money,
    wyckoff,
)


# Per-school weights — sum doesn't need to equal 1, we normalize.
WEIGHTS: dict[str, float] = {
    "classical_ta":  0.10,
    "price_action":  0.13,
    "smart_money":   0.18,
    "wyckoff":       0.08,
    "elliott_wave":  0.08,
    "harmonic":      0.08,
    "fundamental":   0.13,
    "news_analysis": 0.08,
    "divergence":    0.14,
}


# --- structural helpers -------------------------------------------------

def _atr(df: pd.DataFrame, period: int = 14) -> float:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def _swing_points(df: pd.DataFrame, lookback: int = 3) -> tuple[list[int], list[int]]:
    highs, lows = [], []
    h, l = df["high"].values, df["low"].values
    for i in range(lookback, len(df) - lookback):
        if h[i] == max(h[i - lookback:i + lookback + 1]):
            highs.append(i)
        if l[i] == min(l[i - lookback:i + lookback + 1]):
            lows.append(i)
    return highs, lows


def _structural_levels(df: pd.DataFrame, side: str, atr: float, close: float):
    """Pick the best Stop-Loss anchor based on market structure, plus the
    Fibonacci-extension based TP levels."""
    highs_idx, lows_idx = _swing_points(df, lookback=3)
    pad = 0.2 * atr   # small buffer beyond the structural point

    if side == "BUY":
        # Last meaningful swing low — fall back to 30-bar low if no pivot found
        if lows_idx:
            swing_low = float(df["low"].iloc[lows_idx[-1]])
        else:
            swing_low = float(df["low"].iloc[-30:].min())
        sl = min(swing_low - pad, close - 1.2 * atr)
        risk = max(close - sl, atr * 0.5)  # never use a zero/negative risk
        # Fibonacci extensions of the (recent) measured swing
        anchor_high = float(df["high"].iloc[-30:].max())
        anchor_low = swing_low
        leg = max(anchor_high - anchor_low, atr)
        tp1 = close + risk * 1.0                         # 1R conservative
        tp2 = close + max(leg * 0.618, risk * 2.0)       # 1.618 extension or 2R
        tp3 = close + max(leg * 1.0,   risk * 3.0)       # 2.618 extension or 3R
    else:  # SELL
        if highs_idx:
            swing_high = float(df["high"].iloc[highs_idx[-1]])
        else:
            swing_high = float(df["high"].iloc[-30:].max())
        sl = max(swing_high + pad, close + 1.2 * atr)
        risk = max(sl - close, atr * 0.5)
        anchor_high = swing_high
        anchor_low = float(df["low"].iloc[-30:].min())
        leg = max(anchor_high - anchor_low, atr)
        tp1 = close - risk * 1.0
        tp2 = close - max(leg * 0.618, risk * 2.0)
        tp3 = close - max(leg * 1.0,   risk * 3.0)

    return close, sl, tp1, tp2, tp3, risk


def _entry_sl_tp(df: pd.DataFrame, side: str) -> tuple[float, float, float, float, float]:
    atr = _atr(df, 14)
    close = float(df["close"].iloc[-1])
    entry, sl, tp1, tp2, tp3, _risk = _structural_levels(df, side, atr, close)
    return entry, sl, tp1, tp2, tp3


# --- core aggregator ----------------------------------------------------

def aggregate(df: pd.DataFrame, symbol: str = "XAUUSD") -> dict[str, Any]:
    outputs = {
        "classical_ta":  classical_ta.analyze(df),
        "price_action":  price_action.analyze(df),
        "smart_money":   smart_money.analyze(df),
        "wyckoff":       wyckoff.analyze(df),
        "elliott_wave":  elliott_wave.analyze(df),
        "harmonic":      harmonic.analyze(df),
        "fundamental":   fundamental.analyze(df, symbol=symbol),
        "news_analysis": news_analysis.analyze(df, symbol=symbol),
        "divergence":    divergence.analyze(df),
    }

    total_w = sum(WEIGHTS.values())
    score = 0.0
    confidence = 0.0
    aligned = 0
    for name, eo in outputs.items():
        w = WEIGHTS.get(name, 0.0) / total_w
        score += eo.score * w
        confidence += eo.confidence * w
        if abs(eo.score) > 0.15:
            aligned += 1

    side = "BUY" if score >= 0 else "SELL"
    entry, sl, tp1, tp2, tp3 = _entry_sl_tp(df, side)

    raw_strength = (abs(score) * 0.6 + confidence * 0.3 + (aligned / len(outputs)) * 0.1)
    strength = float(np.clip(round(raw_strength * 10, 1), 1.0, 10.0))

    regime = classify_regime(df)
    base_prob = 45 + raw_strength * 30
    if regime == "trending" and abs(score) > 0.2:
        base_prob += 5
    if regime == "ranging":
        base_prob -= 4
    if regime == "reversal":
        base_prob -= 3
    win_prob = float(np.clip(round(base_prob, 1), 30.0, 92.0))

    rationale = {
        name: {
            "score": round(eo.score, 3),
            "confidence": round(eo.confidence, 3),
            "notes": eo.notes,
            "signals": eo.signals,
            "weight": round(WEIGHTS.get(name, 0.0) / total_w, 3),
        }
        for name, eo in outputs.items()
    }

    return {
        "side": side,
        "entry": round(entry, 4),
        "sl": round(sl, 4),
        "tp1": round(tp1, 4),
        "tp2": round(tp2, 4),
        "tp3": round(tp3, 4),
        "strength": strength,
        "win_probability": win_prob,
        "regime": regime,
        "composite_score": round(score, 4),
        "composite_confidence": round(confidence, 4),
        "aligned_schools": aligned,
        "total_schools": len(outputs),
        "rationale": rationale,
    }


# --- Multi-Timeframe Confluence -----------------------------------------

# Each timeframe gets a weight reflecting how predictive it tends to be.
MTF_TIMEFRAMES = [
    ("M15", 0.10),
    ("H1",  0.30),
    ("H4",  0.35),
    ("D1",  0.25),
]


def aggregate_mtf(symbol: str = "XAUUSD") -> dict[str, Any]:
    """Run the aggregator on multiple timeframes, then fuse them.

    A signal that aligns across M15+H1+H4+D1 is dramatically higher conviction
    than a single-timeframe call. We weight the H1/H4 most because they're the
    natural swing-trading frames for our target instruments.
    """
    from app.data.market_feed import fetch_ohlcv  # lazy to avoid cycles

    per_tf: dict[str, dict[str, Any]] = {}
    for tf, _w in MTF_TIMEFRAMES:
        df = fetch_ohlcv(symbol, tf, lookback=200)
        per_tf[tf] = aggregate(df, symbol=symbol)

    # Direction agreement
    buys = sum(1 for tf, r in per_tf.items() if r["side"] == "BUY")
    sells = len(per_tf) - buys
    majority = "BUY" if buys >= sells else "SELL"
    confluence = max(buys, sells)               # how many TFs agree (out of 4)
    confluence_pct = round(confluence / len(per_tf) * 100, 1)

    # Weighted composite across TFs (with sign per direction)
    weighted_score = 0.0
    weighted_conf = 0.0
    total_w = sum(w for _, w in MTF_TIMEFRAMES)
    for tf, w in MTF_TIMEFRAMES:
        r = per_tf[tf]
        signed = r["composite_score"]
        # Treat scores opposite to the majority as negative contributions.
        if r["side"] != majority:
            signed = -abs(signed)
        weighted_score += signed * (w / total_w)
        weighted_conf += r["composite_confidence"] * (w / total_w)

    # Use the H1 timeframe as the *execution* frame for entry/SL/TP, but boost
    # the strength based on confluence across TFs.
    primary = per_tf["H1"].copy()
    primary["side"] = majority

    boost = (confluence - 1) * 0.05   # +5% per extra agreeing TF (max +15%)
    new_strength = float(np.clip(primary["strength"] * (1 + boost), 1.0, 10.0))
    new_win = float(np.clip(primary["win_probability"] + (confluence - 2) * 3.5, 30.0, 95.0))

    primary["strength"] = round(new_strength, 1)
    primary["win_probability"] = round(new_win, 1)
    primary["mtf"] = {
        "confluence": confluence,
        "total_timeframes": len(per_tf),
        "confluence_pct": confluence_pct,
        "majority_side": majority,
        "weighted_score": round(weighted_score, 4),
        "weighted_confidence": round(weighted_conf, 4),
        "per_timeframe": {tf: {"side": r["side"],
                                "strength": r["strength"],
                                "win_probability": r["win_probability"],
                                "composite_score": r["composite_score"]}
                          for tf, r in per_tf.items()},
    }
    return primary
