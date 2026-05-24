"""Yahoo Finance market data provider via yfinance.

Maps our symbol notation to Yahoo tickers and returns standardized OHLCV.
We try a primary ticker first, then alternates — Gold is the trickiest because
GC=F (futures) sometimes returns empty during off-hours while XAUUSD=X (spot)
keeps refreshing on FX hours.

Includes a short TTL cache so repeated calls don't hammer Yahoo.
"""
from __future__ import annotations

import time
from typing import Optional

import pandas as pd


# Primary + fallback tickers per symbol. We try them in order until one returns
# real data. Spot FX tickers (XAUUSD=X) often work when futures (GC=F) don't.
SYMBOL_TICKERS: dict[str, list[str]] = {
    "XAUUSD": ["GC=F", "XAUUSD=X", "XAU=X"],
    "XAGUSD": ["SI=F", "XAGUSD=X", "XAG=X"],
    "WTIUSD": ["CL=F", "WTI=F"],
    "EURUSD": ["EURUSD=X", "EUR=X"],
    "GBPUSD": ["GBPUSD=X", "GBP=X"],
    "USDJPY": ["USDJPY=X", "JPY=X"],
    "AUDUSD": ["AUDUSD=X", "AUD=X"],
    "USDCAD": ["USDCAD=X", "CAD=X"],
    "BTCUSD": ["BTC-USD"],
}

# Back-compat — first ticker per symbol.
SYMBOL_MAP: dict[str, str] = {k: v[0] for k, v in SYMBOL_TICKERS.items()}

# Our timeframe → (yfinance interval, yfinance period)
TIMEFRAME_MAP: dict[str, tuple[str, str]] = {
    "M5":  ("5m",  "30d"),
    "M15": ("15m", "60d"),
    "M30": ("30m", "60d"),
    "H1":  ("60m", "60d"),
    "H4":  ("60m", "60d"),
    "D1":  ("1d",  "2y"),
}


_CACHE: dict[tuple[str, str], tuple[float, pd.DataFrame]] = {}
_CACHE_TTL_SECONDS = 60
_LAST_ERROR: dict[str, str] = {}


def is_available(symbol: str) -> bool:
    return symbol.upper() in SYMBOL_TICKERS


def last_error_for(symbol: str) -> str | None:
    return _LAST_ERROR.get(symbol.upper())


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


def _fetch_one(ticker: str, interval: str, period: str) -> Optional[pd.DataFrame]:
    """Try a single ticker via two yfinance methods. Returns None on failure."""
    try:
        import yfinance as yf
    except ImportError:
        _LAST_ERROR["__yfinance__"] = "yfinance not installed"
        return None

    # 1) yf.download — works for most tickers but can be flaky for futures
    try:
        raw = yf.download(
            tickers=ticker, period=period, interval=interval,
            auto_adjust=False, progress=False, threads=False,
        )
        if raw is not None and not raw.empty:
            return _normalize(raw)
    except Exception as e:
        _LAST_ERROR[ticker] = f"download: {type(e).__name__}: {e}"

    # 2) Ticker.history — alternate path, more reliable for futures sometimes
    try:
        t = yf.Ticker(ticker)
        raw = t.history(period=period, interval=interval, auto_adjust=False)
        if raw is not None and not raw.empty:
            return _normalize(raw)
    except Exception as e:
        _LAST_ERROR[ticker] = f"history: {type(e).__name__}: {e}"

    if ticker not in _LAST_ERROR:
        _LAST_ERROR[ticker] = "empty response"
    return None


def _normalize(raw: pd.DataFrame) -> pd.DataFrame:
    """Flatten columns + rename to our standard schema."""
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [c[0] for c in raw.columns]
    raw = raw.rename(columns={
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume",
    })
    raw = raw.dropna(subset=["open", "high", "low", "close"])
    if raw.empty:
        return raw
    df = raw.reset_index()
    time_col = "Datetime" if "Datetime" in df.columns else ("Date" if "Date" in df.columns else df.columns[0])
    df = df.rename(columns={time_col: "time"})
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df[["time", "open", "high", "low", "close", "volume"]]
    df["volume"] = df["volume"].fillna(0.0).astype(float)
    return df


def fetch_ohlcv(symbol: str, timeframe: str, lookback: int = 200) -> Optional[pd.DataFrame]:
    """Fetch real OHLCV from Yahoo Finance with multi-ticker fallback."""
    symbol = symbol.upper()
    timeframe = timeframe.upper()
    if symbol not in SYMBOL_TICKERS:
        return None
    if timeframe not in TIMEFRAME_MAP:
        timeframe = "H1"

    cached = _from_cache((symbol, timeframe))
    if cached is not None:
        return cached.tail(lookback).reset_index(drop=True)

    interval, period = TIMEFRAME_MAP[timeframe]

    df: Optional[pd.DataFrame] = None
    for ticker in SYMBOL_TICKERS[symbol]:
        df = _fetch_one(ticker, interval, period)
        if df is not None and len(df) > 0:
            _LAST_ERROR.pop(symbol, None)
            break

    if df is None or df.empty:
        return None

    # Resample H1 → H4 if requested
    if timeframe == "H4":
        df = df.set_index("time")
        df = df.resample("4H").agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum",
        }).dropna().reset_index()

    _put_cache((symbol, timeframe), df)
    return df.tail(lookback).reset_index(drop=True)


def diagnose(symbol: str = "XAUUSD") -> dict:
    """Try every fallback ticker and report what worked and what failed."""
    symbol = symbol.upper()
    results = []
    if symbol not in SYMBOL_TICKERS:
        return {"symbol": symbol, "error": "unsupported symbol"}

    try:
        import yfinance as yf
        yf_version = getattr(yf, "__version__", "unknown")
    except ImportError:
        return {"symbol": symbol, "yfinance": "NOT INSTALLED"}

    for ticker in SYMBOL_TICKERS[symbol]:
        info = {"ticker": ticker, "download_ok": False, "history_ok": False,
                "rows": 0, "error": None}
        try:
            raw = yf.download(tickers=ticker, period="5d", interval="1h",
                              auto_adjust=False, progress=False, threads=False)
            info["download_ok"] = raw is not None and not raw.empty
            info["rows"] = 0 if raw is None else len(raw)
        except Exception as e:
            info["error"] = f"download: {type(e).__name__}: {e}"
        try:
            t = yf.Ticker(ticker)
            raw = t.history(period="5d", interval="1h", auto_adjust=False)
            info["history_ok"] = raw is not None and not raw.empty
            if info["rows"] == 0:
                info["rows"] = 0 if raw is None else len(raw)
        except Exception as e:
            if not info["error"]:
                info["error"] = f"history: {type(e).__name__}: {e}"
        results.append(info)

    return {"symbol": symbol, "yfinance": yf_version, "attempts": results}
