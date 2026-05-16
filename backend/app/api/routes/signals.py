"""Signal generation + retrieval."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.aggregator import aggregate
from app.core.config import settings
from app.data.market_feed import SUPPORTED_SYMBOLS, fetch_ohlcv
from app.db import get_db
from app.models.signal import Signal
from app.schemas.signal import GenerateSignalRequest, SignalOut

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.post("/generate", response_model=SignalOut)
def generate(payload: GenerateSignalRequest, db: Session = Depends(get_db)):
    if payload.symbol.upper() not in SUPPORTED_SYMBOLS:
        raise HTTPException(status_code=400, detail=f"unsupported symbol: {payload.symbol}")
    df = fetch_ohlcv(payload.symbol, payload.timeframe, payload.lookback)
    result = aggregate(df, symbol=payload.symbol)

    sig = Signal(
        symbol=payload.symbol.upper(),
        timeframe=payload.timeframe.upper(),
        side=result["side"],
        entry=result["entry"],
        sl=result["sl"],
        tp1=result["tp1"],
        tp2=result["tp2"],
        tp3=result["tp3"],
        strength=result["strength"],
        win_probability=result["win_probability"],
        regime=result["regime"],
        rationale=result["rationale"],
    )
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig


@router.get("/latest", response_model=list[SignalOut])
def latest(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(Signal).order_by(Signal.created_at.desc()).limit(limit).all()
    return rows


@router.get("/{signal_id}", response_model=SignalOut)
def get_one(signal_id: int, db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s:
        raise HTTPException(status_code=404, detail="signal not found")
    return s


@router.get("/symbols/all")
def list_symbols():
    return {"symbols": SUPPORTED_SYMBOLS, "threshold": settings.signal_strength_threshold}
