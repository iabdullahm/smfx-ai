"""Harmonic patterns — Gartley, Bat, Butterfly, Crab (simplified)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.engines.base import EngineOutput
from app.engines.elliott_wave import _zigzag

# Ideal Fibonacci ratios per pattern (XA, AB=BC ratio of XA, BC of AB, CD of BC).
_PATTERNS = {
    "Gartley":   {"AB_XA": 0.618, "BC_AB": (0.382, 0.886), "CD_BC": (1.272, 1.618), "AD_XA": 0.786},
    "Bat":       {"AB_XA": 0.382, "BC_AB": (0.382, 0.886), "CD_BC": (1.618, 2.618), "AD_XA": 0.886},
    "Butterfly": {"AB_XA": 0.786, "BC_AB": (0.382, 0.886), "CD_BC": (1.618, 2.618), "AD_XA": 1.272},
    "Crab":      {"AB_XA": 0.618, "BC_AB": (0.382, 0.886), "CD_BC": (2.240, 3.618), "AD_XA": 1.618},
}


def _within(value: float, target: float, tol: float = 0.08) -> bool:
    return abs(value - target) <= tol


def _within_range(value: float, rng: tuple[float, float], tol: float = 0.08) -> bool:
    lo, hi = rng
    return (lo - tol) <= value <= (hi + tol)


def analyze(df: pd.DataFrame) -> EngineOutput:
    out = EngineOutput(name="harmonic")
    if len(df) < 60:
        out.notes.append("بيانات غير كافية للأنماط التوافقية")
        return out.clamp()

    pivots = _zigzag(df, threshold=0.008)
    if len(pivots) < 5:
        out.notes.append("لم يكتمل نمط XABCD بعد")
        out.confidence = 0.2
        return out.clamp()

    X, A, B, C, D = pivots[-5:]
    xa = abs(A[1] - X[1])
    ab = abs(B[1] - A[1])
    bc = abs(C[1] - B[1])
    cd = abs(D[1] - C[1])
    ad = abs(D[1] - X[1])
    if xa == 0:
        out.notes.append("XA = 0، يتعذر القياس")
        return out.clamp()

    ab_xa = ab / xa
    bc_ab = bc / max(ab, 1e-9)
    cd_bc = cd / max(bc, 1e-9)
    ad_xa = ad / xa

    matched: list[str] = []
    for name, ratios in _PATTERNS.items():
        if (_within(ab_xa, ratios["AB_XA"]) and
                _within_range(bc_ab, ratios["BC_AB"]) and
                _within_range(cd_bc, ratios["CD_BC"]) and
                _within(ad_xa, ratios["AD_XA"], tol=0.10)):
            matched.append(name)

    # Direction: if pattern ends at L (low) it's bullish, H it's bearish.
    direction_bullish = D[2] == "L"
    score = 0.0
    if matched:
        score = 0.5 if direction_bullish else -0.5
        for m in matched:
            out.notes.append(f"نمط توافقي مكتشف: {m} ({'صاعد' if direction_bullish else 'هابط'})")
        out.signals.append({"patterns": matched, "direction": "bullish" if direction_bullish else "bearish"})
    else:
        out.notes.append("لا يوجد نمط توافقي واضح حالياً")

    out.score = score
    out.confidence = 0.7 if matched else 0.25
    return out.clamp()
