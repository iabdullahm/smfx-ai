from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class NewsEvent(Base):
    __tablename__ = "news_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(8))      # USD / EUR / JPY ...
    impact: Mapped[str] = mapped_column(String(8))        # low / medium / high
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    actual: Mapped[str] = mapped_column(String(32), default="")
    forecast: Mapped[str] = mapped_column(String(32), default="")
    previous: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
