"""AI aggregator — combine 8 engines into a final trade signal.

Strategy:
1. Run each engine on the OHLCV frame.
2. Apply per-school weights (configurable).
3. Compute composite score (-1..+1) and composite confidence (0..1).
4. Map composite score → BUY/SELL direction.
5. Derive Entry/SL/TP from market structure (ATR + recent S/R).
6. Compute Signal Strength (1..10) and Win Probability (%).
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np
import pandas as pd

from app.ai.regime import classify_regime
from app.engines import (
    base as _base,  # noqa: F401
)
from app.engines import (
    classical_ta,
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
    "classical_ta": 0.10,
    "price_action": 0.15,
    "smart_money":  0.20,
    "wyckoff":      0.10,
    "elliott_wave": 0.10,
    "harmonic":     0.10,
    "fundamental":  0.15,
    "news_analysis": 0.10,
}


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def _entry_sl_tp(df: pd.DataFrame, side: str) -> tuple[float, float, float, float, float]:
    atr = _atr(df, 14)
    close = float(df["close"].iloc[-1])
    recent_high = float(df["high"].iloc[-30:].max())
    recent_low = float(df["low"].iloc[-30:].min())

    if side == "BUY":
        entry = close
        sl = min(recent_low, close - 1.5 * atr)
        risk = entry - sl
        tp1 = entry + 1.0 * risk
        tp2 = entry + 2.0 * risk
        tp3 = entry + 3.0 * risk
    else:  # SELL
        entry = close
        sl = max(recent_high, close + 1.5 * atr)
        risk = sl - entry
        tp1 = entry - 1.0 * risk
        tp2 = entry - 2.0 * risk
        tp3 = entry - 3.0 * risk
    return entry, sl, tp1, tp2, tp3


def aggregate(df: pd.DataFrame, symbol: str = "XAUUSD") -> dict[str, Any]:
    # Run engines
    outputs = {
        "classical_ta": classical_ta.analyze(df),
        "price_action": price_action.analyze(df),
        "smart_money":  smart_money.analyze(df),
        "wyckoff":      wyckoff.analyze(df),
        "elliott_wave": elliott_wave.analyze(df),
        "harmonic":     harmonic.analyze(df),
        "fundamental":  fundamental.analyze(df, symbol=symbol),
        "news_analysis": news_analysis.analyze(df, symbol=symbol),
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

    # Side & metrics
    side = "BUY" if score >= 0 else "SELL"
    entry, sl, tp1, tp2, tp3 = _entry_sl_tp(df, side)

    # Signal strength (1..10): function of |score|, confidence, and alignment.
    raw_strength = (abs(score) * 0.6 + confidence * 0.3 + (aligned / 8) * 0.1)
    strength = float(np.clip(round(raw_strength * 10, 1), 1.0, 10.0))

    # Win probability (%): mapped from strength + slight noise based on regime
    regime = classify_regime(df)
    base_prob = 45 + raw_strength * 30
    if regime == "trending" and abs(score) > 0.2:
        base_prob += 5
    if regime == "ranging":
        base_prob -= 4
    if regime == "reversal":
        base_prob -= 3
    win_prob = float(np.clip(round(base_prob, 1), 30.0, 92.0))

    # Build rationale (per-engine breakdown for the UI)
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
        "rationale": rationale,
    }
