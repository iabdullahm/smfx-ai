"""Smart Money / ICT concepts: Order Blocks, FVG, Liquidity Sweeps."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.engines.base import EngineOutput


def _find_fvg(df: pd.DataFrame) -> list[dict]:
    """Three-candle Fair Value Gap detection.
    Bullish FVG: low[i] > high[i-2]. Bearish FVG: high[i] < low[i-2].
    """
    fvgs: list[dict] = []
    h, l = df["high"].values, df["low"].values
    for i in range(2, len(df)):
        if l[i] > h[i - 2]:
            fvgs.append({"type": "bullish", "top": float(l[i]), "bottom": float(h[i - 2]), "idx": int(i)})
        elif h[i] < l[i - 2]:
            fvgs.append({"type": "bearish", "top": float(l[i - 2]), "bottom": float(h[i]), "idx": int(i)})
    return fvgs[-5:]  # last few


def _order_blocks(df: pd.DataFrame) -> list[dict]:
    """Simple OB heuristic: the last bearish candle before a strong bullish impulse
    (and vice-versa) is a candidate Order Block."""
    blocks: list[dict] = []
    if len(df) < 10:
        return blocks
    body = (df["close"] - df["open"]).values
    avg_body = np.mean(np.abs(body[-50:])) if len(df) >= 50 else np.mean(np.abs(body))
    impulse_threshold = avg_body * 1.8
    for i in range(2, len(df) - 1):
        # Bullish OB: bearish candle followed by big bullish candle
        if body[i] < 0 and body[i + 1] > impulse_threshold:
            blocks.append({
                "type": "bullish_ob",
                "top": float(df["high"].iloc[i]),
                "bottom": float(df["low"].iloc[i]),
                "idx": int(i),
            })
        elif body[i] > 0 and body[i + 1] < -impulse_threshold:
            blocks.append({
                "type": "bearish_ob",
                "top": float(df["high"].iloc[i]),
                "bottom": float(df["low"].iloc[i]),
                "idx": int(i),
            })
    return blocks[-5:]


def _liquidity_sweep(df: pd.DataFrame) -> str | None:
    """Detect a wick that took out a recent swing high/low then reversed."""
    if len(df) < 20:
        return None
    last = df.iloc[-1]
    win = df.iloc[-20:-1]
    if last["high"] > win["high"].max() and last["close"] < win["high"].max():
        return "bearish_sweep"   # took liquidity above then closed below → sells
    if last["low"] < win["low"].min() and last["close"] > win["low"].min():
        return "bullish_sweep"   # took liquidity below then closed above → buys
    return None


def analyze(df: pd.DataFrame) -> EngineOutput:
    out = EngineOutput(name="smart_money")
    if len(df) < 30:
        out.notes.append("بيانات غير كافية لـ Smart Money / ICT")
        return out.clamp()

    last_close = float(df["close"].iloc[-1])
    score = 0.0

    fvgs = _find_fvg(df)
    obs = _order_blocks(df)
    sweep = _liquidity_sweep(df)

    # Score by sweep
    if sweep == "bullish_sweep":
        score += 0.5
        out.notes.append("Liquidity Sweep صاعد (اصطياد بائعين ثم انعكاس)")
    elif sweep == "bearish_sweep":
        score -= 0.5
        out.notes.append("Liquidity Sweep هابط (اصطياد مشترين ثم انعكاس)")

    # Score by nearest OB
    nearest_ob = None
    for ob in obs:
        mid = (ob["top"] + ob["bottom"]) / 2
        dist = abs(last_close - mid) / max(last_close, 1e-9)
        if dist < 0.01:  # within 1%
            nearest_ob = ob
            break
    if nearest_ob:
        if nearest_ob["type"] == "bullish_ob":
            score += 0.3
            out.notes.append("السعر داخل Bullish Order Block")
        else:
            score -= 0.3
            out.notes.append("السعر داخل Bearish Order Block")

    # FVG bias (unfilled recent)
    open_fvgs = [f for f in fvgs if (f["type"] == "bullish" and last_close > f["bottom"]) or
                 (f["type"] == "bearish" and last_close < f["top"])]
    if open_fvgs:
        latest = open_fvgs[-1]
        if latest["type"] == "bullish":
            score += 0.2
            out.notes.append("Bullish FVG لم يُملأ بعد")
        else:
            score -= 0.2
            out.notes.append("Bearish FVG لم يُملأ بعد")

    out.signals.append({"order_blocks": obs})
    out.signals.append({"fvgs": fvgs})
    out.signals.append({"liquidity_sweep": sweep})

    out.score = float(np.clip(score, -1.0, 1.0))
    out.confidence = min(1.0, 0.5 + abs(out.score) * 0.4)
    return out.clamp()
