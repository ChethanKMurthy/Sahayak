"""Database setup + ORM models.

Privacy-shaped per docs/ARCHITECTURE.md §8:
  - sessions are ephemeral (TTL), storing working JSON state
  - documents persist METADATA ONLY; no full Aadhaar number is ever written
  - audit_log is append-only DPDP evidence
Defaults to SQLite for local dev; set DATABASE_URL to Postgres/RDS for cloud.
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Base(DeclarativeBase):
    pass


class SessionRow(Base):
    """Ephemeral working state for one assisted session."""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    owner: Mapped[str] = mapped_column(String(120), default="guest")  # operator/user id
    language: Mapped[str] = mapped_column(String(8), default="hi")
    state: Mapped[str] = mapped_column(String(32), default="capture")
    # full working payload (documents meta, field values, eligibility, fill...) as JSON
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    audits: Mapped[list["AuditRow"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class AuditRow(Base):
    """Append-only: what was read, asked, confirmed — DPDP evidence."""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"))
    at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    action: Mapped[str] = mapped_column(String(48))   # read|ask|answer|consent|output|...
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    session: Mapped[SessionRow] = relationship(back_populates="audits")


class TrackingRow(Base):
    """Post-submission follow-up: reference number, where, reminders."""
    __tablename__ = "tracking"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    owner: Mapped[str] = mapped_column(String(120), default="guest")
    scheme_id: Mapped[str] = mapped_column(String(64))
    form_template_id: Mapped[str] = mapped_column(String(64))
    reference_number: Mapped[str] = mapped_column(String(120), default="")
    submitted_to: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft|submitted|...
    pdf_url: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reminders: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)


class RejectionRow(Base):
    """Rejection-reason learning loop raw input."""
    __tablename__ = "rejection_feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scheme_id: Mapped[str] = mapped_column(String(64))
    form_template_id: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(32), default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    suggested_validation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
