from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project: Mapped[str] = mapped_column(String(120), index=True)
    reviewer: Mapped[str] = mapped_column(String(120), default="anonymous")
    language: Mapped[str] = mapped_column(String(40), default="unknown")
    source: Mapped[str] = mapped_column(String(40), default="diff")
    pr_url: Mapped[str] = mapped_column(String(500), default="")
    diff_text: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text)
    memory_json: Mapped[str] = mapped_column(Text)
    memory_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(Integer, index=True)
    finding_id: Mapped[str] = mapped_column(String(40))
    decision: Mapped[str] = mapped_column(String(30))
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
