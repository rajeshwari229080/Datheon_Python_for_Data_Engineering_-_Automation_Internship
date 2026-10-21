"""Lightweight in-process task scheduler using Python schedule library.
Provides thread-safe periodic execution, clean signal shutdowns, and prevents concurrent runs.
"""
import logging
import signal
import sys
import threading
import time
from typing import Callable, Optional
import schedule
from src.pipeline.orchestrator import EtlOrchestrator

logger = logging.getLogger(__name__)


class EtlScheduler:
    """Manages periodic execution of the ETL orchestrator pipeline."""

    def __init__(
        self,
        interval_minutes: int = 60,
        orchestrator: Optional[EtlOrchestrator] = None,
        dry_run: bool = False
    ):
        self.interval_minutes = interval_minutes
        self.orchestrator = orchestrator or EtlOrchestrator()
        self.dry_run = dry_run
        self._stop_event = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._job = None

    def _job_wrapper(self) -> None:
        """Execute scheduled pipeline job with exception isolation."""
        logger.info(f"Triggering scheduled ETL pipeline run (Interval: {self.interval_minutes}m)...")
        try:
            state = self.orchestrator.run_pipeline(dry_run=self.dry_run)
            logger.info(f"Scheduled pipeline run completed with status: {state.status} (Duration: {state.duration_seconds}s)")
        except Exception as e:
            logger.error(f"Scheduled pipeline execution error: {e}", exc_info=True)

    def start_in_background(self) -> None:
        """Start scheduler in a background daemon thread."""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            logger.warning("Scheduler thread is already running.")
            return

        self._stop_event.clear()
        schedule.clear()
        self._job = schedule.every(self.interval_minutes).minutes.do(self._job_wrapper)

        def run_loop():
            logger.info(f"Background scheduler loop started. Polling every {self.interval_minutes} minutes.")
            while not self._stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)
            logger.info("Background scheduler loop cleanly terminated.")

        self._scheduler_thread = threading.Thread(target=run_loop, daemon=True)
        self._scheduler_thread.start()

    def stop(self) -> None:
        """Signal background scheduler to stop and wait for loop termination."""
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            logger.info("Stopping scheduler background thread...")
            self._stop_event.set()
            self._scheduler_thread.join(timeout=3)
            self._scheduler_thread = None
            schedule.clear()
            logger.info("Scheduler successfully stopped.")

    def run_blocking(self) -> None:
        """Run blocking scheduler in main thread with graceful SIGINT/SIGTERM handlers."""
        schedule.clear()
        self._job = schedule.every(self.interval_minutes).minutes.do(self._job_wrapper)
        logger.info(f"Starting blocking scheduler. Every {self.interval_minutes} minutes. Press Ctrl+C to exit.")

        # Trigger first run immediately on startup
        logger.info("Executing immediate initial pipeline run on schedule startup...")
        self._job_wrapper()

        def signal_handler(sig, frame):
            logger.info("Received termination signal. Exiting scheduler cleanly...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler shutdown complete.")
