"""Elliott Wave — simplified wave-count heuristic on zigzag pivots."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.engines.base import EngineOutput


def _zigzag(df: pd.DataFrame, threshold: float = 0.01) -> list[tuple[int, float, str]]:
    """Return list of (idx, price, kind) where kind in {'H','L'} alternating."""
    pivots: list[tuple[int, float, str]] = []
    if len(df) < 5:
        return pivots
    last_pivot_price = df["close"].iloc[0]
    last_pivot_idx = 0
    direction: str | None = None  # 'up' or 'down'

    for i in range(1, len(df)):
        price = df["close"].iloc[i]
        change = (price - last_pivot_price) / max(last_pivot_price, 1e-9)
        if direction is None:
            if abs(change) >= threshold:
                direction = "up" if change > 0 else "down"
                pivots.append((last_pivot_idx, last_pivot_price, "L" if direction == "up" else "H"))
                last_pivot_idx, last_pivot_price = i, price
        elif direction == "up":
            if price > last_pivot_price:
                last_pivot_idx, last_pivot_price = i, price
            elif (last_pivot_price - price) / last_pivot_price >= threshold:
                pivots.append((last_pivot_idx, last_pivot_price, "H"))
                direction = "down"
                last_pivot_idx, last_pivot_price = i, price
        else:  # down
            if price < last_pivot_price:
                last_pivot_idx, last_pivot_price = i, price
            elif (price - last_pivot_price) / last_pivot_price >= threshold:
                pivots.append((last_pivot_idx, last_pivot_price, "L"))
                direction = "up"
                last_pivot_idx, last_pivot_price = i, price

    pivots.append((last_pivot_idx, last_pivot_price, "H" if direction == "up" else "L"))
    return pivots


def analyze(df: pd.DataFrame) -> EngineOutput:
    out = EngineOutput(name="elliott_wave")
    if len(df) < 60:
        out.notes.append("بيانات غير كافية لـ Elliott Wave")
        return out.clamp()

    pivots = _zigzag(df, threshold=0.008)
    if len(pivots) < 5:
        out.notes.append("الموجات غير واضحة بعد")
        out.confidence = 0.2
        return out.clamp()

    # Look at the last 5 pivots
    last5 = pivots[-5:]
    kinds = "".join(k for _, _, k in last5)
    # Bullish impulse pattern signature: L H L H L H ...
    bullish_impulse = kinds in ("LHLHL", "LHLHLH", "HLHLH")
    bearish_impulse = kinds in ("HLHLH", "HLHLHL", "LHLHL"[::-1])

    score = 0.0
    label = "موجة غير محددة"
    if kinds.endswith("L") and bullish_impulse:
        score = 0.5
        label = "ختام موجة تصحيحية، توقع موجة دافعة صاعدة"
    elif kinds.endswith("H") and bearish_impulse:
        score = -0.5
        label = "ختام موجة تصحيحية، توقع موجة دافعة هابطة"
    else:
        # weak directional bias by last leg
        prev_price, last_price = last5[-2][1], last5[-1][1]
        change = (last_price - prev_price) / max(prev_price, 1e-9)
        score = float(np.tanh(change * 10))

    out.score = score
    out.confidence = 0.4 + min(0.4, len(pivots) / 30)
    out.signals.append({"pivots": [(p[0], round(p[1], 4), p[2]) for p in last5]})
    out.notes.append(f"Elliott: {label}")
    return out.clamp()
