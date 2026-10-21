"""Standalone entry point for Project 4: Scheduled End-to-End ETL Pipeline with Alerting.
Can be executed directly via:
    python projects/project_4_scheduled_etl/run.py
"""
import argparse
import logging
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.reporting.generator import configure_pipeline_logger
from src.pipeline.orchestrator import EtlOrchestrator
from src.pipeline.scheduler import EtlScheduler

logger = configure_pipeline_logger("logs/pipeline.log", log_level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="DataFlow Project 4: Scheduled End-to-End ETL Pipeline")
    parser.add_argument("--schedule", action="store_true", help="Run in periodic scheduled mode")
    parser.add_argument("--interval", type=int, default=60, help="Interval in minutes for scheduler (default: 60)")
    parser.add_argument("--dry-run", action="store_true", help="Execute transformations and roll back database writes")
    parser.add_argument("--live", action="store_true", help="Force live web scraping rather than local fixtures")
    args = parser.parse_args()

    orchestrator = EtlOrchestrator()

    if args.schedule:
        logger.info(f"Starting scheduled execution mode every {args.interval} minutes...")
        scheduler = EtlScheduler(
            interval_minutes=args.interval,
            orchestrator=orchestrator,
            dry_run=args.dry_run
        )
        scheduler.run_blocking()
    else:
        logger.info(f"Triggering immediate single pipeline execution (Dry-Run: {args.dry_run})...")
        state = orchestrator.run_pipeline(
            dry_run=args.dry_run,
            force_live_scrape=args.live
        )

        print(f"""
============================================================
ETL PIPELINE EXECUTION SUMMARY
============================================================
Run ID:             {state.run_id}
Pipeline:           {state.pipeline_name}
Status:             {state.status} (Dry Run: {state.dry_run})
Execution Window:   {state.started_at} -> {state.ended_at}
Duration:           {state.duration_seconds}s

Records Summary:
  - Extracted:      {state.records_extracted}
  - Cleaned:        {state.records_cleaned}
  - Inserted:       {state.records_inserted}
  - Updated:        {state.records_updated}
  - Unchanged:      {state.records_unchanged}
  - Failed:         {state.records_failed}
  - Error:          {state.error_message or 'None'}
============================================================""")

        if state.status == "FAILED":
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
