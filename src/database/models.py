"""SQLAlchemy 2.0 declarative database models and schema definitions.
Features strict typing, unique business key constraints, and performance indexes.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JobPosting(Base):
    """Job postings relational entity with deterministic fingerprint unique key."""

    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_hash = Column(String(64), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    organization = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True, default="Remote")
    category = Column(String(100), nullable=True, index=True, default="Engineering")
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True, default="USD")
    posted_date = Column(Date, nullable=True)
    source_url = Column(String(1024), nullable=False)
    extracted_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_job_title_org", "title", "organization"),
        Index("ix_job_category_loc", "category", "location"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "record_hash": self.record_hash,
            "title": self.title,
            "organization": self.organization,
            "location": self.location,
            "category": self.category,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "currency": self.currency,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "source_url": self.source_url,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EtlRunRecord(Base):
    """ETL execution telemetry and audit log entity."""

    __tablename__ = "etl_run_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), nullable=False, unique=True, index=True)
    pipeline_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # SUCCESS, FAILED, DRY_RUN
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    records_extracted = Column(Integer, default=0)
    records_cleaned = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_unchanged = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "pipeline_name": self.pipeline_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "records_extracted": self.records_extracted,
            "records_cleaned": self.records_cleaned,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "records_unchanged": self.records_unchanged,
            "records_failed": self.records_failed,
            "error_message": self.error_message,
        }
