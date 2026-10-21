"""Standalone entry point for Project 3: Relational Database Auto-Ingestion & Upsert Engine.
Can be executed directly via:
    python projects/project_3_database_ingestion/run.py
"""
import argparse
from datetime import datetime, timezone
import json
import logging
import os
import sys
import time
from typing import Optional
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.database.engine import DatabaseEngineFactory
from src.database.upsert import DatabaseUpsertEngine
from src.database.verifier import DatabaseQueryVerifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("project_3_database_ingestion")


def run_database_ingestion(
    input_file: Optional[str] = None,
    database_url: Optional[str] = None,
    batch_size: int = 50,
    dry_run: bool = False,
    report_path: str = "reports/database_load_report.json"
) -> dict:
    """Execute end-to-end database loading with idempotent upserts and verification."""
    start_time = time.perf_counter()

    # 1. Connect & initialize tables
    db_factory = DatabaseEngineFactory(database_url=database_url)
    db_factory.create_tables()

    # Check connection health
    if not db_factory.ping():
        raise ConnectionError("Database health check ping failed.")

    session = db_factory.get_session()
    records = []

    # 2. Load input dataset
    if input_file:
        abs_input = os.path.join(REPO_ROOT, input_file) if not os.path.isabs(input_file) else input_file
    else:
        abs_input = os.path.join(REPO_ROOT, "data/processed/cleaned_jobs.csv")

    if os.path.exists(abs_input):
        logger.info(f"Loading data to ingest from: {abs_input}")
        if abs_input.endswith(".json"):
            df = pd.read_json(abs_input)
        else:
            df = pd.read_csv(abs_input)
        # Convert NaN values to None for clean SQLAlchemy binding
        records = df.where(pd.notnull(df), None).to_dict(orient="records")
    else:
        logger.warning(f"Input file not found: {abs_input}. Running verification queries on existing database.")

    # 3. Perform batch upsert
    upsert_engine = DatabaseUpsertEngine(session=session, batch_size=batch_size)
    metrics = upsert_engine.upsert_records(records, dry_run=dry_run)
    metrics.duration_seconds = round(time.perf_counter() - start_time, 3)

    # 4. Run Analytical Query Verification
    verifier = DatabaseQueryVerifier(session=session)
    verification = verifier.run_full_verification()

    session.close()

    # 5. Compile and export report
    report_data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "database_url": db_factory._mask_url(db_factory.database_url),
        "dry_run": dry_run,
        "input_source": abs_input if os.path.exists(abs_input) else "Existing DB",
        "ingestion_metrics": {
            "total_processed": metrics.total_processed,
            "inserted": metrics.inserted,
            "updated": metrics.updated,
            "unchanged": metrics.unchanged,
            "failed": metrics.failed,
            "batches_executed": metrics.batch_count,
            "duration_seconds": metrics.duration_seconds
        },
        "database_state": {
            "total_table_records": verification.total_records,
            "unique_record_hashes": verification.unique_record_hashes,
            "duplicate_records_found": verification.duplicate_records_found,
            "rollback_test_passed": verification.rollback_test_passed,
            "categories_breakdown": verification.categories_breakdown,
            "top_organizations": verification.top_organizations[:5],
            "salary_statistics": verification.salary_stats
        }
    }

    abs_report = os.path.join(REPO_ROOT, report_path) if not os.path.isabs(report_path) else report_path
    os.makedirs(os.path.dirname(abs_report), exist_ok=True)
    with open(abs_report, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    logger.info(f"Database load report saved to: {abs_report}")

    print(f"""============================================================
DATABASE INGESTION & QUERY VERIFICATION SUMMARY
============================================================
Database:            {report_data['database_url']} (Dry Run: {dry_run})
Total Processed:     {metrics.total_processed}
Inserted:            {metrics.inserted}
Updated in Place:    {metrics.updated}
Unchanged:           {metrics.unchanged}
Failed:              {metrics.failed}
Execution Duration:  {metrics.duration_seconds}s

Final Table Records: {verification.total_records}
Duplicate Hashes:    {verification.duplicate_records_found} (Must be 0)
Rollback Test:       {'PASSED' if verification.rollback_test_passed else 'FAILED'}
Categories Tracked:  {len(verification.categories_breakdown)}
============================================================""")

    return report_data


def main():
    parser = argparse.ArgumentParser(description="DataFlow Project 3: Relational Database Auto-Ingestion & Upsert Engine")
    parser.add_argument("--input", help="Path to cleaned input CSV/JSON file")
    parser.add_argument("--db-url", help="Database connection URL (defaults to SQLite)")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for upsert transactions")
    parser.add_argument("--dry-run", action="store_true", help="Simulate upserts and rollback without committing")
    parser.add_argument("--report", default="reports/database_load_report.json", help="Path to database load report")
    args = parser.parse_args()

    try:
        run_database_ingestion(
            input_file=args.input,
            database_url=args.db_url,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            report_path=args.report
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal database ingestion error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
