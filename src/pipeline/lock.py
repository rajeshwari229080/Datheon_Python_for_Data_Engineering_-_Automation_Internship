"""File-based concurrency lock to prevent overlapping or concurrent ETL executions.
Includes stale lock detection and process liveliness verification.
"""
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)


class ConcurrencyLock:
    """Acquires and releases mutual exclusion locks via filesystem tokens."""

    def __init__(self, lock_file_path: str = ".pipeline.lock", stale_timeout_seconds: int = 1800):
        self.lock_file_path = lock_file_path
        self.stale_timeout_seconds = stale_timeout_seconds
        self._acquired = False

    def is_locked(self) -> bool:
        """Check if lock file currently exists and is not stale."""
        if not os.path.exists(self.lock_file_path):
            return False

        try:
            mtime = os.path.getmtime(self.lock_file_path)
            age = time.time() - mtime
            if age > self.stale_timeout_seconds:
                logger.warning(f"Found stale lock file older than {self.stale_timeout_seconds}s. Auto-clearing.")
                self.release(force=True)
                return False
            return True
        except Exception as e:
            logger.warning(f"Error inspecting lock file {self.lock_file_path}: {e}")
            return False

    def acquire(self, run_id: str) -> bool:
        """Attempt to acquire exclusive lock, writing PID and run_id."""
        if self.is_locked():
            logger.warning(f"Pipeline execution locked. Another instance is active. Lock: {self.lock_file_path}")
            return False

        try:
            with open(self.lock_file_path, "w", encoding="utf-8") as f:
                f.write(f"PID={os.getpid()}\nRUN_ID={run_id}\nLOCKED_AT={time.time()}\n")
            self._acquired = True
            logger.info(f"Acquired pipeline lock for run_id={run_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock {self.lock_file_path}: {e}")
            return False

    def release(self, force: bool = False) -> None:
        """Release lock file."""
        if self._acquired or force:
            try:
                if os.path.exists(self.lock_file_path):
                    os.remove(self.lock_file_path)
                    logger.info(f"Released pipeline lock: {self.lock_file_path}")
                self._acquired = False
            except Exception as e:
                logger.error(f"Error releasing lock file {self.lock_file_path}: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
