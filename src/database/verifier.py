"""Analytical query verification and transaction validation suite.
Executes aggregation, sorting, filtering, duplicate audits, and verifies rollback safety.
"""
from dataclasses import asdict, dataclass, field
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from src.database.models import JobPosting

logger = logging.getLogger(__name__)


@dataclass
class VerificationSummary:
    total_records: int = 0
    unique_record_hashes: int = 0
    duplicate_records_found: int = 0
    categories_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    top_organizations: List[Dict[str, Any]] = field(default_factory=list)
    salary_stats: Dict[str, Any] = field(default_factory=dict)
    rollback_test_passed: bool = False


class DatabaseQueryVerifier:
    """Verifies relational integrity, query performance, and transactional safety."""

    def __init__(self, session: Session):
        self.session = session

    def get_row_count(self) -> int:
        """Return total number of rows in job_postings table."""
        stmt = select(func.count(JobPosting.id))
        return self.session.scalar(stmt) or 0

    def check_duplicates(self) -> Tuple[int, int]:
        """Verify business key uniqueness. Returns (total_rows, duplicate_count)."""
        total = self.get_row_count()
        stmt_distinct = select(func.count(func.distinct(JobPosting.record_hash)))
        distinct_count = self.session.scalar(stmt_distinct) or 0
        duplicates = total - distinct_count
        return total, duplicates

    def get_category_aggregations(self) -> List[Dict[str, Any]]:
        """Calculate counts and average compensation grouped by job category."""
        stmt = (
            select(
                JobPosting.category,
                func.count(JobPosting.id).label("job_count"),
                func.round(func.avg(JobPosting.salary_min), 2).label("avg_min_salary"),
                func.round(func.avg(JobPosting.salary_max), 2).label("avg_max_salary")
            )
            .group_by(JobPosting.category)
            .order_by(text("job_count DESC"))
        )
        results = []
        for row in self.session.execute(stmt):
            results.append({
                "category": row.category,
                "job_count": row.job_count,
                "avg_min_salary": float(row.avg_min_salary) if row.avg_min_salary else None,
                "avg_max_salary": float(row.avg_max_salary) if row.avg_max_salary else None,
            })
        return results

    def get_top_organizations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find companies with highest active job openings."""
        stmt = (
            select(
                JobPosting.organization,
                func.count(JobPosting.id).label("openings")
            )
            .group_by(JobPosting.organization)
            .order_by(text("openings DESC"))
            .limit(limit)
        )
        return [{"organization": row.organization, "openings": row.openings} for row in self.session.execute(stmt)]

    def get_salary_statistics(self) -> Dict[str, Any]:
        """Aggregate system-wide salary statistics."""
        stmt = select(
            func.min(JobPosting.salary_min).label("min_sal"),
            func.max(JobPosting.salary_max).label("max_sal"),
            func.round(func.avg(JobPosting.salary_min), 2).label("avg_sal"),
            func.count(JobPosting.salary_min).label("salaries_reported")
        )
        row = self.session.execute(stmt).first()
        if row:
            return {
                "min_salary": float(row.min_sal) if row.min_sal else None,
                "max_salary": float(row.max_sal) if row.max_sal else None,
                "avg_salary": float(row.avg_sal) if row.avg_sal else None,
                "salaries_reported": row.salaries_reported
            }
        return {}

    def filter_and_sort_jobs(
        self,
        min_salary: Optional[float] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        search_keyword: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Execute filtered and sorted search query demonstrating complex analytical querying."""
        stmt = select(JobPosting)

        if min_salary is not None:
            stmt = stmt.where(JobPosting.salary_min >= min_salary)
        if category:
            stmt = stmt.where(JobPosting.category.ilike(f"%{category}%"))
        if location:
            stmt = stmt.where(JobPosting.location.ilike(f"%{location}%"))
        if search_keyword:
            stmt = stmt.where(
                JobPosting.title.ilike(f"%{search_keyword}%") |
                JobPosting.organization.ilike(f"%{search_keyword}%")
            )

        stmt = stmt.order_by(JobPosting.salary_min.desc().nullslast()).limit(limit)
        return [job.to_dict() for job in self.session.scalars(stmt)]

    def verify_transaction_rollback(self) -> bool:
        """Prove that transactional failures roll back cleanly without leaving orphan data."""
        test_hash = "__ROLLBACK_INTEGRITY_TEST_HASH__"
        # Ensure clean state
        self.session.query(JobPosting).filter(JobPosting.record_hash == test_hash).delete()
        self.session.commit()

        initial_count = self.get_row_count()
        try:
            # Stage 1: Add row inside transaction
            test_row = JobPosting(
                record_hash=test_hash,
                title="Rollback Test Job",
                organization="Rollback Labs",
                location="Remote",
                category="Testing",
                source_url="https://example.com/test",
                extracted_at=func.now()
            )
            self.session.add(test_row)
            self.session.flush()

            # Stage 2: Intentionally trigger exception before commit
            raise RuntimeError("Simulated transaction crash for rollback validation")
        except RuntimeError:
            self.session.rollback()

        # Stage 3: Assert database row count is completely unchanged
        final_count = self.get_row_count()
        orphan_row = self.session.query(JobPosting).filter(JobPosting.record_hash == test_hash).first()

        rollback_succeeded = (initial_count == final_count and orphan_row is None)
        logger.info(f"Transaction rollback verification status: {rollback_succeeded}")
        return rollback_succeeded

    def run_full_verification(self) -> VerificationSummary:
        """Execute all validation checks and return structured summary."""
        total, dups = self.check_duplicates()
        summary = VerificationSummary(
            total_records=total,
            unique_record_hashes=total - dups,
            duplicate_records_found=dups,
            categories_breakdown=self.get_category_aggregations(),
            top_organizations=self.get_top_organizations(10),
            salary_stats=self.get_salary_statistics(),
            rollback_test_passed=self.verify_transaction_rollback()
        )
        return summary
