from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)         # XAUUSD, EURUSD, ...
    timeframe: Mapped[str] = mapped_column(String(8), default="H1")
    side: Mapped[str] = mapped_column(String(8))                        # BUY / SELL
    entry: Mapped[float] = mapped_column(Float)
    sl: Mapped[float] = mapped_column(Float)
    tp1: Mapped[float] = mapped_column(Float)
    tp2: Mapped[float] = mapped_column(Float)
    tp3: Mapped[float] = mapped_column(Float)
    strength: Mapped[float] = mapped_column(Float)                      # 1..10
    win_probability: Mapped[float] = mapped_column(Float)               # 0..100
    regime: Mapped[str] = mapped_column(String(16), default="trending") # trending/ranging/reversal
    rationale: Mapped[dict] = mapped_column(JSON, default=dict)         # per-engine breakdown
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
