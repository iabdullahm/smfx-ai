"""Detailed per-engine analysis (without persistence)."""
from fastapi import APIRouter, HTTPException, Query

from app.ai.aggregator import aggregate, aggregate_mtf
from app.data.market_feed import SUPPORTED_SYMBOLS, fetch_ohlcv, get_data_source
from app.data import yahoo_feed

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/_diagnose/yahoo/{symbol}")
def yahoo_diagnose(symbol: str):
    """Diagnose Yahoo Finance fetch for a symbol — tries every fallback ticker
    and reports what worked."""
    return yahoo_feed.diagnose(symbol)


@router.get("/{symbol}")
def analyze_symbol(
    symbol: str,
    timeframe: str = Query("H1"),
    lookback: int = Query(200, ge=50, le=1000),
    mtf: bool = Query(False, description="Multi-timeframe confluence (M15+H1+H4+D1)"),
):
    if symbol.upper() not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"unsupported symbol: {symbol}")

    if mtf:
        result = aggregate_mtf(symbol=symbol)
        df = fetch_ohlcv(symbol, "H1", lookback)
    else:
        df = fetch_ohlcv(symbol, timeframe, lookback)
        result = aggregate(df, symbol=symbol)

    candles = df.tail(100).copy()
    candles["time"] = candles["time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result["candles"] = candles[["time", "open", "high", "low", "close", "volume"]].to_dict("records")
    result["symbol"] = symbol.upper()
    result["timeframe"] = "MTF" if mtf else timeframe.upper()
    result["data_source"] = get_data_source(symbol, timeframe)
    return result
