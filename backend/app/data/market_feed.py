"""Market data feed.

For MVP we produce a deterministic synthetic OHLCV series per symbol so the
analysis pipeline can run without external API keys. Real providers (Twelve
Data, Yahoo, CCXT) can be plugged in by replacing `fetch_ohlcv`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd


# Anchor prices for supported instruments (approximate spot, May 2026).
_ANCHOR_PRICES: dict[str, float] = {
    "XAUUSD": 2380.0,    # Gold
    "XAGUSD": 30.40,     # Silver
    "WTIUSD": 78.20,     # Crude oil (WTI)
    "EURUSD": 1.0820,
    "GBPUSD": 1.2710,
    "USDJPY": 152.40,
    "AUDUSD": 0.6620,
    "USDCAD": 1.3640,
    "BTCUSD": 63500.0,
}

_TF_TO_MINUTES: dict[str, int] = {
    "M5": 5, "M15": 15, "M30": 30,
    "H1": 60, "H4": 240, "D1": 1440,
}


def _seed_for(symbol: str, timeframe: str) -> int:
    # Stable seed: same symbol/tf reproduces the same series across calls.
    base = sum(ord(c) for c in f"{symbol}-{timeframe}")
    # Mix in current hour so the feed "advances" but stays stable inside the hour.
    bucket = int(datetime.now(timezone.utc).timestamp() // 3600)
    return base * 31 + bucket


def fetch_ohlcv(symbol: str = "XAUUSD", timeframe: str = "H1",
                lookback: int = 200) -> pd.DataFrame:
    """Return synthetic OHLCV with realistic-looking structure.

    Columns: time, open, high, low, close, volume
    """
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    if symbol not in _ANCHOR_PRICES:
        # Fallback price for unknown symbols.
        _ANCHOR_PRICES[symbol] = 100.0
    if timeframe not in _TF_TO_MINUTES:
        timeframe = "H1"

    minutes = _TF_TO_MINUTES[timeframe]
    anchor = _ANCHOR_PRICES[symbol]

    rng = np.random.default_rng(_seed_for(symbol, timeframe))

    # Generate log-returns with a regime mix (trend + mean-reversion) and bursts.
    drift = rng.normal(0.0, 0.0002, lookback)
    vol = np.abs(rng.normal(0.0, 0.0030, lookback))
    # Occasional shocks (news-like)
    shocks = rng.choice([0, 0, 0, 0, 1], size=lookback) * rng.normal(0, 0.006, lookback)
    # Trend block
    trend_strength = rng.uniform(-0.0005, 0.0005)
    trend = np.linspace(0, trend_strength * lookback, lookback)

    log_returns = drift + vol * rng.standard_normal(lookback) + shocks + (trend / lookback)
    prices = anchor * np.exp(np.cumsum(log_returns))

    # Build OHLC bars from per-bar mini-walk
    opens = prices.copy()
    closes = np.roll(prices, -1)
    closes[-1] = prices[-1] * (1 + rng.normal(0, 0.0005))
    high_offset = np.abs(rng.normal(0, 0.0015, lookback)) * prices
    low_offset = np.abs(rng.normal(0, 0.0015, lookback)) * prices
    highs = np.maximum(opens, closes) + high_offset
    lows = np.minimum(opens, closes) - low_offset
    volumes = rng.integers(800, 5000, lookback).astype(float)

    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    times = [end - timedelta(minutes=minutes * (lookback - i - 1)) for i in range(lookback)]

    df = pd.DataFrame({
        "time": times,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })
    return df


SUPPORTED_SYMBOLS = list(_ANCHOR_PRICES.keys())
