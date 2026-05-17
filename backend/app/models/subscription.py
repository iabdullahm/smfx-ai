from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan: Mapped[str] = mapped_column(String(32), default="monthly")   # monthly / annual / trial
    status: Mapped[str] = mapped_column(String(16), default="pending") # pending / active / cancelled / expired
    amount_usd: Mapped[float] = mapped_column(Float, default=0.0)
    payment_provider: Mapped[str] = mapped_column(String(32), default="")      # nowpayments / stripe / manual
    payment_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    payment_status: Mapped[str] = mapped_column(String(32), default="")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
