from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SignalBase(BaseModel):
    symbol: str
    timeframe: str = "H1"
    side: str
    entry: float
    sl: float
    tp1: float
    tp2: float
    tp3: float
    strength: float = Field(ge=0, le=10)
    win_probability: float = Field(ge=0, le=100)
    regime: str = "trending"
    rationale: dict = Field(default_factory=dict)


class SignalCreate(SignalBase):
    pass


class SignalOut(SignalBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateSignalRequest(BaseModel):
    symbol: str = Field(default="XAUUSD", description="مثال: XAUUSD, XAGUSD, WTIUSD, EURUSD")
    timeframe: str = Field(default="H1", description="M15, H1, H4, D1")
    lookback: int = Field(default=200, ge=50, le=1000)
