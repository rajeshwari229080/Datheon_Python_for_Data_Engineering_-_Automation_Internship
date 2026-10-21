"""End-to-end integration and system tests for Project 4: Scheduled ETL Pipeline."""
import json
import os
import pytest
from src.pipeline.lock import ConcurrencyLock
from src.pipeline.orchestrator import EtlOrchestrator
from src.notifications.notifier import NotificationManager


def test_concurrency_lock_lifecycle(tmp_path):
    lock_file = str(tmp_path / "test.lock")
    lock1 = ConcurrencyLock(lock_file)
    lock2 = ConcurrencyLock(lock_file)

    # 1. Acquire first lock
    assert lock1.acquire("run_001") is True
    assert lock1.is_locked() is True

    # 2. Second lock acquisition must fail
    assert lock2.acquire("run_002") is False

    # 3. Release first lock
    lock1.release()
    assert lock1.is_locked() is False

    # 4. Second lock can now acquire
    assert lock2.acquire("run_002") is True
    lock2.release()


def test_pipeline_dry_run_execution():
    orchestrator = EtlOrchestrator()
    state = orchestrator.run_pipeline(dry_run=True, force_live_scrape=False)

    assert state.status == "DRY_RUN"
    assert state.dry_run is True
    assert state.records_extracted >= 100
    assert state.records_cleaned >= 100
    assert "extract" in state.stages
    assert state.stages["extract"].status == "COMPLETED"
    assert state.stages["load_upsert"].status == "COMPLETED"
    assert state.stages["verify"].status == "COMPLETED"


def test_pipeline_live_e2e_execution():
    orchestrator = EtlOrchestrator()
    state = orchestrator.run_pipeline(dry_run=False, force_live_scrape=False)

    assert state.status == "SUCCESS"
    assert state.records_extracted >= 100
    assert state.records_cleaned >= 100
    assert state.records_inserted >= 0
    assert state.duration_seconds > 0.0

    # Verify run history was persisted in reports/run_history.json
    history_file = "reports/run_history.json"
    assert os.path.exists(history_file)
    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)
    assert len(history) > 0
    assert history[0]["run_id"] == state.run_id


def test_notification_console_fallback():
    notifier = NotificationManager()
    class DummyState:
        run_id = "test_run_123"
        pipeline_name = "Test Pipeline"
        status = "SUCCESS"
        dry_run = False
        started_at = "2026-10-21 12:00:00"
        ended_at = "2026-10-21 12:00:02"
        duration_seconds = 2.0
        records_extracted = 125
        records_cleaned = 125
        records_inserted = 125
        records_updated = 0
        records_unchanged = 0
        records_failed = 0
        error_message = None
        stages = {}

    results = notifier.send_pipeline_alert(DummyState())
    assert "console" in results
    assert results["console"] is True
