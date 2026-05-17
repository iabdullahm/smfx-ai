"""Yahoo Finance market data provider via yfinance.

Maps our symbol notation (XAUUSD, EURUSD, …) to Yahoo tickers (GC=F, EURUSD=X, …)
and returns the standard OHLCV DataFrame with columns: time, open, high, low,
close, volume.

Includes a simple in-process TTL cache so repeated calls inside the same minute
don't hammer Yahoo (≈ rate-limit safety + lower latency).
"""
from __future__ import annotations

import time
from typing import Optional

import pandas as pd


# Our symbol → Yahoo Finance ticker.
SYMBOL_MAP: dict[str, str] = {
    "XAUUSD": "GC=F",        # Gold continuous futures
    "XAGUSD": "SI=F",        # Silver continuous futures
    "WTIUSD": "CL=F",        # Crude Oil WTI continuous futures
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "BTCUSD": "BTC-USD",
}

# Our timeframe → (yfinance interval, yfinance period)
# yfinance limits: 1m intraday → max 7d. 5m/15m/30m/1h → max 60d.
TIMEFRAME_MAP: dict[str, tuple[str, str]] = {
    "M5":  ("5m",  "30d"),
    "M15": ("15m", "60d"),
    "M30": ("30m", "60d"),
    "H1":  ("60m", "60d"),
    "H4":  ("60m", "60d"),   # fetched as 1h then resampled to 4h
    "D1":  ("1d",  "2y"),
}


# Simple TTL cache: {(symbol, tf): (timestamp, dataframe)}
_CACHE: dict[tuple[str, str], tuple[float, pd.DataFrame]] = {}
_CACHE_TTL_SECONDS = 60   # refresh every minute


def _from_cache(key: tuple[str, str]) -> Optional[pd.DataFrame]:
    item = _CACHE.get(key)
    if not item:
        return None
    ts, df = item
    if time.time() - ts < _CACHE_TTL_SECONDS:
        return df.copy()
    return None


def _put_cache(key: tuple[str, str], df: pd.DataFrame) -> None:
    _CACHE[key] = (time.time(), df.copy())


def is_available(symbol: str) -> bool:
    return symbol.upper() in SYMBOL_MAP


def fetch_ohlcv(symbol: str, timeframe: str, lookback: int = 200) -> Optional[pd.DataFrame]:
    """Fetch real OHLCV from Yahoo Finance.

    Returns None on any failure (caller should fall back to synthetic feed).
    """
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    if symbol not in SYMBOL_MAP:
        return None
    if timeframe not in TIMEFRAME_MAP:
        timeframe = "H1"

    cached = _from_cache((symbol, timeframe))
    if cached is not None:
        # Trim to requested lookback
        return cached.tail(lookback).reset_index(drop=True)

    try:
        import yfinance as yf  # lazy import — keeps cold-start light
    except ImportError:
        return None

    ticker = SYMBOL_MAP[symbol]
    interval, period = TIMEFRAME_MAP[timeframe]

    try:
        raw = yf.download(
            tickers=ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception:
        return None

    if raw is None or raw.empty:
        return None

    # yfinance returns a MultiIndex column on single-ticker downloads in newer versions.
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [c[0] for c in raw.columns]

    raw = raw.rename(columns={
        "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"
    })

    # Resample to H4 if requested (yfinance has no 4h native).
    if timeframe == "H4":
        raw = raw.resample("4H").agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna()

    raw = raw.dropna(subset=["open", "high", "low", "close"])
    if raw.empty:
        return None

    df = raw.reset_index()
    # Standardize the time column name
    time_col = "Datetime" if "Datetime" in df.columns else ("Date" if "Date" in df.columns else df.columns[0])
    df = df.rename(columns={time_col: "time"})

    # Ensure UTC and tz-aware
    df["time"] = pd.to_datetime(df["time"], utc=True)

    df = df[["time", "open", "high", "low", "close", "volume"]]
    df["volume"] = df["volume"].fillna(0.0).astype(float)

    _put_cache((symbol, timeframe), df)
    return df.tail(lookback).reset_index(drop=True)
