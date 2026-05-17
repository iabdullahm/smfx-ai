"""Backtesting endpoint."""
from fastapi import APIRouter, HTTPException, Query

from app.backtest.engine import report_to_dict, run_backtest
from app.data.market_feed import SUPPORTED_SYMBOLS

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.get("/{symbol}")
def backtest(
    symbol: str,
    timeframe: str = Query("H1"),
    lookback: int = Query(800, ge=200, le=2000),
    forward_window: int = Query(30, ge=5, le=120),
    min_strength: float = Query(5.0, ge=1.0, le=10.0),
    step: int = Query(3, ge=1, le=20),
    include_log: bool = Query(False),
):
    if symbol.upper() not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"unsupported symbol: {symbol}")

    rep = run_backtest(
        symbol=symbol.upper(),
        timeframe=timeframe.upper(),
        lookback=lookback,
        forward_window=forward_window,
        min_strength=min_strength,
        step=step,
    )
    return report_to_dict(rep, include_log=include_log)
