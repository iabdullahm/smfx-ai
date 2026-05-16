"""Market regime classifier: trending / ranging / reversal."""
from __future__ import annotations

import numpy as np
import pandas as pd


def classify_regime(df: pd.DataFrame) -> str:
    if len(df) < 50:
        return "unknown"
    close = df["close"]
    # ADX-like proxy
    diffs = close.diff().dropna()
    abs_move = diffs.abs().rolling(20).sum().iloc[-1]
    net_move = abs(close.iloc[-1] - close.iloc[-20])
    efficiency = float(net_move / max(abs_move, 1e-9))

    # Volatility regime
    vol = close.pct_change().rolling(20).std().iloc[-1]
    recent_vol = close.pct_change().iloc[-5:].std()

    if efficiency > 0.4:
        return "trending"
    if recent_vol > vol * 1.6:
        return "reversal"
    return "ranging"
