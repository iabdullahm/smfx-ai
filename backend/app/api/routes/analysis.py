"""Detailed per-engine analysis (without persistence)."""
from fastapi import APIRouter, HTTPException, Query

from app.ai.aggregator import aggregate
from app.data.market_feed import SUPPORTED_SYMBOLS, fetch_ohlcv

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/{symbol}")
def analyze_symbol(
    symbol: str,
    timeframe: str = Query("H1"),
    lookback: int = Query(200, ge=50, le=1000),
):
    if symbol.upper() not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"unsupported symbol: {symbol}")
    df = fetch_ohlcv(symbol, timeframe, lookback)
    result = aggregate(df, symbol=symbol)
    # Last 100 candles for charting
    candles = df.tail(100).copy()
    candles["time"] = candles["time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result["candles"] = candles[["time", "open", "high", "low", "close", "volume"]].to_dict("records")
    result["symbol"] = symbol.upper()
    result["timeframe"] = timeframe.upper()
    return result
