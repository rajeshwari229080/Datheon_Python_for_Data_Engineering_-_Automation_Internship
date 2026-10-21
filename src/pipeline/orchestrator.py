"""Multi-stage ETL orchestrator engine.
Coordinates end-to-end data lifecycle:
Extract -> Validate Input -> Transform -> Validate Output -> Load/Upsert -> Verify -> Report -> Notify
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional
import pandas as pd

from src.scraper.client import PoliteHttpClient
from src.scraper.extractor import HtmlExtractor
from src.scraper.dedup import RecordDeduplicator, export_records_to_csv, export_records_to_json
from src.cleaner.normalizer import ColumnNormalizer
from src.cleaner.type_parsers import StringSanitizer
from src.cleaner.currency_parsers import CurrencyParser
from src.cleaner.date_parsers import DateNormalizer
from src.cleaner.validator import SchemaValidator
from src.cleaner.reporter import DataQualityReporter
from src.database.engine import DatabaseEngineFactory
from src.database.upsert import DatabaseUpsertEngine
from src.database.verifier import DatabaseQueryVerifier
from src.database.models import EtlRunRecord
from src.pipeline.lock import ConcurrencyLock
from src.notifications.notifier import NotificationManager

logger = logging.getLogger(__name__)


@dataclass
class StageStatus:
    name: str
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, SKIPPED
    started_at: str = ""
    ended_at: str = ""
    duration_seconds: float = 0.0
    records_in: int = 0
    records_out: int = 0
    message: str = ""


@dataclass
class PipelineExecutionState:
    run_id: str
    pipeline_name: str
    status: str = "PENDING"  # PENDING, RUNNING, SUCCESS, FAILED, PARTIAL, DRY_RUN
    dry_run: bool = False
    started_at: str = ""
    ended_at: str = ""
    duration_seconds: float = 0.0
    stages: Dict[str, StageStatus] = field(default_factory=dict)
    records_extracted: int = 0
    records_cleaned: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_unchanged: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    output_artifacts: Dict[str, str] = field(default_factory=dict)


class EtlOrchestrator:
    """End-to-end pipeline orchestrator managing execution stages, locks, and history."""

    def __init__(
        self,
        config_path: str = "config/pipeline_config.json",
        repo_root: Optional[str] = None
    ):
        self.repo_root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        abs_cfg = os.path.join(self.repo_root, config_path) if not os.path.isabs(config_path) else config_path
        
        with open(abs_cfg, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.pipeline_name = self.config.get("pipeline_name", "DataFlow E2E Pipeline")
        self.lock = ConcurrencyLock(
            os.path.join(self.repo_root, self.config.get("execution", {}).get("concurrency_lock_file", ".pipeline.lock"))
        )
        self.db_factory = DatabaseEngineFactory(os.getenv("DATABASE_URL", "sqlite:///database/dataflow.db"))
        self.notifier = NotificationManager()

    def generate_run_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_uuid = uuid.uuid4().hex[:6]
        return f"run_{timestamp}_{short_uuid}"

    def run_pipeline(
        self,
        dry_run: bool = False,
        force_live_scrape: bool = False
    ) -> PipelineExecutionState:
        """Execute end-to-end pipeline workflow with mutual exclusion and state tracking."""
        run_id = self.generate_run_id()
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        state = PipelineExecutionState(
            run_id=run_id,
            pipeline_name=self.pipeline_name,
            status="RUNNING",
            dry_run=dry_run,
            started_at=now_iso,
        )
        t_start = time.perf_counter()

        stage_names = [
            "extract", "validate_input", "transform", "validate_output",
            "load_upsert", "verify", "report", "notify"
        ]
        for name in stage_names:
            state.stages[name] = StageStatus(name=name)

        # Acquire concurrency lock
        if not self.lock.acquire(run_id):
            state.status = "FAILED"
            state.error_message = "Could not acquire concurrency lock. Another ETL pipeline instance is running."
            return state

        raw_records = []
        cleaned_df = pd.DataFrame()
        ingestion_metrics = None
        db_verification = None

        try:
            # ------------------------------------------------------------------
            # 1. EXTRACT STAGE
            # ------------------------------------------------------------------
            stg = state.stages["extract"]
            stg.status = "RUNNING"
            stg.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            t_stg = time.perf_counter()

            from projects.project_1_scraper.run import run_scraper
            scraper_summary = run_scraper(
                config_path="config/scraper_config.json",
                force_live=force_live_scrape
            )
            raw_csv_path = os.path.join(self.repo_root, "data/raw/scraped_jobs.csv")
            if os.path.exists(raw_csv_path):
                raw_df = pd.read_csv(raw_csv_path)
                raw_records = raw_df.to_dict(orient="records")

            stg.records_out = len(raw_records)
            stg.duration_seconds = round(time.perf_counter() - t_stg, 3)
            stg.status = "COMPLETED"
            stg.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            state.records_extracted = len(raw_records)

            # ------------------------------------------------------------------
            # 2. VALIDATE INPUT STAGE
            # ------------------------------------------------------------------
            stg = state.stages["validate_input"]
            stg.status = "RUNNING"
            stg.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            t_stg = time.perf_counter()

            if not raw_records:
                raise ValueError("Extract stage produced 0 records. Input validation failed.")

            stg.records_in = len(raw_records)
            stg.records_out = len(raw_records)
            stg.duration_seconds = round(time.perf_counter() - t_stg, 3)
            stg.status = "COMPLETED"
            stg.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # ------------------------------------------------------------------
            # 3. TRANSFORM & CLEAN STAGE
            # ------------------------------------------------------------------
            stg = state.stages["transform"]
            stg.status = "RUNNING"
            stg.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            t_stg = time.perf_counter()

            from projects.project_2_data_cleaning.run import clean_dataset
            clean_summary = clean_dataset(
                input_path="data/raw/scraped_jobs.csv",
                schema_path="config/schema.json",
                output_csv_path="data/processed/cleaned_jobs.csv",
                output_json_path="data/processed/cleaned_jobs.json"
            )
            processed_csv_path = os.path.join(self.repo_root, "data/processed/cleaned_jobs.csv")
            cleaned_df = pd.read_csv(processed_csv_path)

            stg.records_in = len(raw_records)
            stg.records_out = len(cleaned_df)
            stg.duration_seconds = round(time.perf_counter() - t_stg, 3)
            stg.status = "COMPLETED"
            stg.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            state.records_cleaned = len(cleaned_df)

            # ------------------------------------------------------------------
            # 4. VALIDATE OUTPUT STAGE
            # ------------------------------------------------------------------
            stg = state.stages["validate_output"]
            stg.status = "RUNNING"
            stg.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            t_stg = time.perf_counter()

            if len(cleaned_df) == 0:
                raise ValueError("Transformation stage produced 0 valid records.")

            stg.records_in = len(cleaned_df)
            stg.records_out = len(cleaned_df)
            stg.duration_seconds = round(time.perf_counter() - t_stg, 3)
            stg.status = "COMPLETED"
            stg.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # ------------------------------------------------------------------
            # 5. LOAD / UPSERT STAGE
            # ------------------------------------------------------------------
            stg = state.stages["load_upsert"]
            stg.status = "RUNNING"
            stg.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            t_stg = time.perf_counter()

            self.db_factory.create_tables()
            session = self.db_factory.get_session()
            upsert_engine = DatabaseUpsertEngine(session, batch_size=50)

            records_to_load = cleaned_df.where(pd.notnull(cleaned_df), None).to_dict(orient="records")
            ingestion_metrics = upsert_engine.upsert_records(records_to_load, dry_run=dry_run)

            state.records_inserted = ingestion_metrics.inserted
            state.records_updated = ingestion_metrics.updated
            state.records_unchanged = ingestion_metrics.unchanged
            state.records_failed = ingestion_metrics.failed

            stg.records_in = len(records_to_load)
            stg.records_out = ingestion_metrics.inserted + ingestion_metrics.updated + ingestion_metrics.unchanged
            stg.duration_seconds = round(time.perf_counter() - t_stg, 3)
            stg.status = "COMPLETED"
            stg.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # ------------------------------------------------------------------
            # 6. VERIFY STAGE
            # ------------------------------------------------------------------
            stg = state.stages["verify"]
            stg.status = "RUNNING"
            stg.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            t_stg = time.perf_counter()

            verifier = DatabaseQueryVerifier(session)
            db_verification = verifier.run_full_verification()
            session.close()

            stg.duration_seconds = round(time.perf_counter() - t_stg, 3)
            stg.status = "COMPLETED"
            stg.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # ------------------------------------------------------------------
            # 7. REPORT & AUDIT STAGE
            # ------------------------------------------------------------------
            stg = state.stages["report"]
            stg.status = "RUNNING"
            stg.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            t_stg = time.perf_counter()

            state.status = "DRY_RUN" if dry_run else "SUCCESS"
            state.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            state.duration_seconds = round(time.perf_counter() - t_start, 3)

            self._save_run_history(state)

            stg.duration_seconds = round(time.perf_counter() - t_stg, 3)
            stg.status = "COMPLETED"
            stg.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            # ------------------------------------------------------------------
            # 8. NOTIFY STAGE
            # ------------------------------------------------------------------
            stg = state.stages["notify"]
            stg.status = "RUNNING"
            stg.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            t_stg = time.perf_counter()

            self.notifier.send_pipeline_alert(state)

            stg.duration_seconds = round(time.perf_counter() - t_stg, 3)
            stg.status = "COMPLETED"
            stg.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        except Exception as e:
            logger.error(f"Pipeline run {run_id} failed: {e}", exc_info=True)
            state.status = "FAILED"
            state.error_message = str(e)
            state.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            state.duration_seconds = round(time.perf_counter() - t_start, 3)
            self._save_run_history(state)
            self.notifier.send_pipeline_alert(state)

        finally:
            self.lock.release()

        return state

    def _save_run_history(self, state: PipelineExecutionState) -> None:
        """Persist execution telemetry in SQLite/PostgreSQL table and JSON history log."""
        # 1. Database table persistence
        try:
            session = self.db_factory.get_session()
            history_record = EtlRunRecord(
                run_id=state.run_id,
                pipeline_name=state.pipeline_name,
                status=state.status,
                started_at=datetime.strptime(state.started_at, "%Y-%m-%d %H:%M:%S"),
                ended_at=datetime.strptime(state.ended_at, "%Y-%m-%d %H:%M:%S") if state.ended_at else None,
                duration_seconds=state.duration_seconds,
                records_extracted=state.records_extracted,
                records_cleaned=state.records_cleaned,
                records_inserted=state.records_inserted,
                records_updated=state.records_updated,
                records_unchanged=state.records_unchanged,
                records_failed=state.records_failed,
                error_message=state.error_message
            )
            session.add(history_record)
            session.commit()
            session.close()
        except Exception as ex:
            logger.warning(f"Could not write run history to DB: {ex}")

        # 2. JSON history file persistence
        try:
            history_file = os.path.join(self.repo_root, "reports/run_history.json")
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            history = []
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    try:
                        history = json.load(f)
                    except Exception:
                        history = []

            # Serialize stage dataclasses
            serialized_state = {
                "run_id": state.run_id,
                "pipeline_name": state.pipeline_name,
                "status": state.status,
                "dry_run": state.dry_run,
                "started_at": state.started_at,
                "ended_at": state.ended_at,
                "duration_seconds": state.duration_seconds,
                "records_extracted": state.records_extracted,
                "records_cleaned": state.records_cleaned,
                "records_inserted": state.records_inserted,
                "records_updated": state.records_updated,
                "records_unchanged": state.records_unchanged,
                "records_failed": state.records_failed,
                "error_message": state.error_message,
                "stages": {k: asdict(v) for k, v in state.stages.items()}
            }
            history.insert(0, serialized_state)
            # Keep last 50 runs
            history = history[:50]

            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

            # Also update pipeline_summary.json with the latest run
            summary_file = os.path.join(self.repo_root, "reports/pipeline_summary.json")
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(serialized_state, f, indent=2)

        except Exception as ex:
            logger.error(f"Error persisting JSON history: {ex}")
