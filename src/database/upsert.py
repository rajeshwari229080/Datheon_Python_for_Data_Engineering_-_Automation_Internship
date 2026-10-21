"""High-performance idempotent upsert engine with batch processing.
Guarantees duplicate-safe inserts, in-place record updates, and rollback isolation.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, date, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.database.models import JobPosting

logger = logging.getLogger(__name__)


@dataclass
class IngestionMetrics:
    total_processed: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    failed: int = 0
    rejected: int = 0
    batch_count: int = 0
    duration_seconds: float = 0.0


class DatabaseUpsertEngine:
    """Manages transactional batch upsert operations into JobPosting table."""

    def __init__(self, session: Session, batch_size: int = 50):
        self.session = session
        self.batch_size = batch_size

    def _parse_date(self, val: Any) -> Optional[date]:
        if not val or pd_isna(val):
            return None
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        try:
            return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
        except Exception:
            return None

    def _parse_datetime(self, val: Any) -> datetime:
        if not val or pd_isna(val):
            return datetime.now(timezone.utc)
        if isinstance(val, datetime):
            return val
        try:
            return datetime.strptime(str(val), "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.now(timezone.utc)

    def upsert_records(
        self, records: List[Dict[str, Any]], dry_run: bool = False
    ) -> IngestionMetrics:
        """Process list of clean record dictionaries into database with idempotent upserts.
        
        Args:
            records: List of dictionaries matching schema.
            dry_run: If True, execute comparison logic without committing database modifications.
            
        Returns:
            IngestionMetrics tallying inserted, updated, unchanged, failed.
        """
        metrics = IngestionMetrics()
        metrics.total_processed = len(records)

        if not records:
            return metrics

        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]
            metrics.batch_count += 1
            self._process_batch(batch, metrics, dry_run=dry_run)

        return metrics

    def _process_batch(
        self, batch: List[Dict[str, Any]], metrics: IngestionMetrics, dry_run: bool
    ) -> None:
        """Process a single atomic batch of records."""
        try:
            record_hashes = [r.get("record_hash") for r in batch if r.get("record_hash")]
            
            # Fetch existing records by hashes
            stmt = select(JobPosting).where(JobPosting.record_hash.in_(record_hashes))
            existing_records = {row.record_hash: row for row in self.session.scalars(stmt)}

            for raw in batch:
                h = raw.get("record_hash")
                if not h:
                    metrics.rejected += 1
                    continue

                if h in existing_records:
                    existing = existing_records[h]
                    has_changes = self._apply_updates_if_changed(existing, raw)
                    if has_changes:
                        metrics.updated += 1
                    else:
                        metrics.unchanged += 1
                else:
                    new_job = self._build_job_model(raw)
                    self.session.add(new_job)
                    metrics.inserted += 1

            if dry_run:
                self.session.rollback()
                logger.info(f"Dry-run active: rolled back batch {metrics.batch_count}")
            else:
                self.session.commit()
                logger.debug(f"Committed batch {metrics.batch_count} of size {len(batch)}")

        except Exception as e:
            self.session.rollback()
            metrics.failed += len(batch)
            logger.error(f"Batch {metrics.batch_count} transaction failed, rolled back: {e}", exc_info=True)
            raise e

    def _build_job_model(self, raw: Dict[str, Any]) -> JobPosting:
        """Construct new JobPosting entity from dictionary."""
        return JobPosting(
            record_hash=str(raw["record_hash"]),
            title=str(raw.get("title", "")),
            organization=str(raw.get("organization", "")),
            location=raw.get("location") or "Remote",
            category=raw.get("category") or "Engineering",
            salary_min=float(raw["salary_min"]) if raw.get("salary_min") not in (None, "", "None") and not pd_isna(raw.get("salary_min")) else None,
            salary_max=float(raw["salary_max"]) if raw.get("salary_max") not in (None, "", "None") and not pd_isna(raw.get("salary_max")) else None,
            currency=raw.get("currency") or "USD",
            posted_date=self._parse_date(raw.get("posted_date")),
            source_url=str(raw.get("source_url", "")),
            extracted_at=self._parse_datetime(raw.get("extracted_at")),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

    def _apply_updates_if_changed(self, existing: JobPosting, raw: Dict[str, Any]) -> bool:
        """Check for field modifications and update existing record if changed."""
        changed = False

        new_title = str(raw.get("title", ""))
        if new_title and existing.title != new_title:
            existing.title = new_title
            changed = True

        new_org = str(raw.get("organization", ""))
        if new_org and existing.organization != new_org:
            existing.organization = new_org
            changed = True

        new_loc = raw.get("location") or "Remote"
        if existing.location != new_loc:
            existing.location = new_loc
            changed = True

        new_cat = raw.get("category") or "Engineering"
        if existing.category != new_cat:
            existing.category = new_cat
            changed = True

        raw_smin = raw.get("salary_min")
        new_smin = float(raw_smin) if raw_smin not in (None, "", "None") and not pd_isna(raw_smin) else None
        if existing.salary_min != new_smin:
            existing.salary_min = new_smin
            changed = True

        raw_smax = raw.get("salary_max")
        new_smax = float(raw_smax) if raw_smax not in (None, "", "None") and not pd_isna(raw_smax) else None
        if existing.salary_max != new_smax:
            existing.salary_max = new_smax
            changed = True

        new_curr = raw.get("currency") or "USD"
        if existing.currency != new_curr:
            existing.currency = new_curr
            changed = True

        new_date = self._parse_date(raw.get("posted_date"))
        if existing.posted_date != new_date:
            existing.posted_date = new_date
            changed = True

        if changed:
            existing.updated_at = datetime.now(timezone.utc)

        return changed


def pd_isna(val: Any) -> bool:
    """Safe null check without requiring pandas import in tight loop."""
    if val is None:
        return True
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return True
    except Exception:
        pass
    return False
