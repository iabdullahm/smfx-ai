"""Market data feed with multi-provider support.

Pipeline:
1. Try the configured live provider (Yahoo Finance via yfinance).
2. If it fails (no network / unsupported symbol / rate-limit), fall back to a
   deterministic synthetic OHLCV series so the analysis pipeline always returns.

The synthetic feed is also useful for backtesting and offline development.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
import pandas as pd

from app.data import yahoo_feed


# Anchor prices for supported instruments (approximate spot, May 2026).
# Used by the synthetic fallback only.
_ANCHOR_PRICES: dict[str, float] = {
    "XAUUSD": 2380.0,
    "XAGUSD": 30.40,
    "WTIUSD": 78.20,
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


# --- Provider config -------------------------------------------------------

# Read from env each call so it can be toggled without restart in dev.
def _live_data_enabled() -> bool:
    val = os.environ.get("USE_LIVE_DATA", "1").lower()
    return val in ("1", "true", "yes", "on")


# --- Synthetic feed (fallback) --------------------------------------------

def _seed_for(symbol: str, timeframe: str) -> int:
    base = sum(ord(c) for c in f"{symbol}-{timeframe}")
    bucket = int(datetime.now(timezone.utc).timestamp() // 3600)
    return base * 31 + bucket


def _fetch_synthetic(symbol: str, timeframe: str, lookback: int) -> pd.DataFrame:
    if symbol not in _ANCHOR_PRICES:
        _ANCHOR_PRICES[symbol] = 100.0
    if timeframe not in _TF_TO_MINUTES:
        timeframe = "H1"

    minutes = _TF_TO_MINUTES[timeframe]
    anchor = _ANCHOR_PRICES[symbol]
    rng = np.random.default_rng(_seed_for(symbol, timeframe))

    drift = rng.normal(0.0, 0.0002, lookback)
    vol = np.abs(rng.normal(0.0, 0.0030, lookback))
    shocks = rng.choice([0, 0, 0, 0, 1], size=lookback) * rng.normal(0, 0.006, lookback)
    trend_strength = rng.uniform(-0.0005, 0.0005)
    trend = np.linspace(0, trend_strength * lookback, lookback)

    log_returns = drift + vol * rng.standard_normal(lookback) + shocks + (trend / lookback)
    prices = anchor * np.exp(np.cumsum(log_returns))

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

    return pd.DataFrame({
        "time": times, "open": opens, "high": highs, "low": lows,
        "close": closes, "volume": volumes,
    })


# --- Public entry point ---------------------------------------------------

def fetch_ohlcv(symbol: str = "XAUUSD", timeframe: str = "H1",
                lookback: int = 200) -> pd.DataFrame:
    """Return OHLCV — live if available, synthetic as fallback.

    Columns: time, open, high, low, close, volume
    """
    symbol = symbol.upper()
    timeframe = timeframe.upper()

    if _live_data_enabled() and yahoo_feed.is_available(symbol):
        df = yahoo_feed.fetch_ohlcv(symbol, timeframe, lookback)
        if df is not None and len(df) >= 50:
            return df

    # Fallback: synthetic
    return _fetch_synthetic(symbol, timeframe, lookback)


def get_data_source(symbol: str = "XAUUSD", timeframe: str = "H1") -> str:
    """Return 'live' or 'synthetic' for the most recent fetch of this pair."""
    if _live_data_enabled() and yahoo_feed.is_available(symbol):
        df = yahoo_feed.fetch_ohlcv(symbol, timeframe, lookback=50)
        if df is not None and len(df) >= 50:
            return "live"
    return "synthetic"


SUPPORTED_SYMBOLS = list(_ANCHOR_PRICES.keys())
