"""Database utilities for persisting alert delivery logs."""
from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import get_database_url


Base = declarative_base()


class AlertMessage(Base):
    """ORM model storing each alert delivery attempt."""

    __tablename__ = "alert_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(50), nullable=False)
    target = Column(Text, nullable=False)
    subject = Column(Text, nullable=True)
    message = Column(Text, nullable=False)
    success = Column(Boolean, nullable=False, default=False)
    error = Column(Text, nullable=True)
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


engine = create_engine(get_database_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create database tables if they do not already exist."""

    Base.metadata.create_all(bind=engine)


def _stringify_target(target: Any) -> str:
    if isinstance(target, str):
        return target
    if isinstance(target, Iterable):
        return ", ".join(str(item) for item in target)
    return str(target)


def _normalize_detail(detail: Any) -> Any:
    if detail is None or isinstance(detail, (dict, list)):
        return detail
    return str(detail)


def create_alert_log(
    *,
    channel: str,
    target: Any,
    message: str,
    subject: str | None,
    success: bool,
    error: str | None,
    detail: Any,
) -> int:
    """Persist an alert delivery attempt and return the new record ID."""

    normalized_target = _stringify_target(target)
    normalized_detail = _normalize_detail(detail)

    with SessionLocal() as session:
        record = AlertMessage(
            channel=channel,
            target=normalized_target,
            subject=subject,
            message=message,
            success=success,
            error=error,
            detail=normalized_detail,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record.id


__all__ = ["AlertMessage", "create_alert_log", "init_db"]
