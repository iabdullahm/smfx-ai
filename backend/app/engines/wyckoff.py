"""Wyckoff market phase detector (simplified heuristic)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.engines.base import EngineOutput


def _phase(df: pd.DataFrame) -> tuple[str, float]:
    """Return (phase, bullishness) where bullishness in [-1, 1]."""
    if len(df) < 50:
        return "unknown", 0.0
    close = df["close"]
    vol = df["volume"]
    window = close.iloc[-50:]
    vol_w = vol.iloc[-50:]

    rng = window.max() - window.min()
    avg = window.mean()
    relative_range = rng / max(avg, 1e-9)

    slope = (window.iloc[-1] - window.iloc[0]) / max(window.iloc[0], 1e-9)
    vol_trend = (vol_w.iloc[-10:].mean() - vol_w.iloc[:10].mean()) / max(vol_w.mean(), 1e-9)

    # Narrow range + flat slope → accumulation or distribution
    if relative_range < 0.04 and abs(slope) < 0.01:
        return ("accumulation" if vol_trend > 0 else "distribution",
                0.2 if vol_trend > 0 else -0.2)
    if slope > 0.02:
        return "markup", 0.6
    if slope < -0.02:
        return "markdown", -0.6
    return "transition", 0.0


def analyze(df: pd.DataFrame) -> EngineOutput:
    out = EngineOutput(name="wyckoff")
    if len(df) < 50:
        out.notes.append("بيانات غير كافية لتحليل Wyckoff")
        return out.clamp()

    phase, bias = _phase(df)
    out.score = float(bias)
    out.confidence = 0.5 if phase != "unknown" else 0.2
    out.signals.append({"phase": phase})
    labels = {
        "accumulation": "مرحلة تجميع — توقع صعود لاحق",
        "markup": "مرحلة صعود — السوق صاعد",
        "distribution": "مرحلة توزيع — توقع هبوط لاحق",
        "markdown": "مرحلة هبوط — السوق هابط",
        "transition": "مرحلة انتقالية — اتجاه غير واضح",
        "unknown": "غير محدد",
    }
    out.notes.append(f"Wyckoff: {labels.get(phase, phase)}")
    return out.clamp()
