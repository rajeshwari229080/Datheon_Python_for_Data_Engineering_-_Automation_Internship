"""Scraping summary reporter and metrics collector.
Tracks extraction telemetry, timing, error tallies, and produces detailed reports.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
import os
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class ScrapingMetrics:
    target_name: str
    source_url: str
    is_fixture: bool
    started_at: str
    ended_at: str = ""
    duration_seconds: float = 0.0
    pages_attempted: int = 0
    pages_successful: int = 0
    pages_failed: int = 0
    records_extracted: int = 0
    duplicates_removed: int = 0
    errors: List[str] = field(default_factory=list)
    output_files: Dict[str, str] = field(default_factory=dict)


class ScrapingReporter:
    """Manages telemetry and report generation for scraping sessions."""

    def __init__(self, target_name: str, source_url: str, is_fixture: bool = False):
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.metrics = ScrapingMetrics(
            target_name=target_name,
            source_url=source_url,
            is_fixture=is_fixture,
            started_at=now_iso,
        )
        self._start_perf = time.perf_counter()

    def record_page_attempt(self) -> None:
        self.metrics.pages_attempted += 1

    def record_page_success(self, count: int) -> None:
        self.metrics.pages_successful += 1
        self.metrics.records_extracted += count

    def record_page_failure(self, error: str) -> None:
        self.metrics.pages_failed += 1
        self.metrics.errors.append(error)

    def record_duplicates(self, count: int) -> None:
        self.metrics.duplicates_removed += count

    def set_output_files(self, paths: Dict[str, str]) -> None:
        self.metrics.output_files = paths

    def finalize(self) -> Dict[str, Any]:
        self.metrics.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.metrics.duration_seconds = round(time.perf_counter() - self._start_perf, 3)
        return asdict(self.metrics)

    def export_report(self, file_path: str = "reports/scraping_summary.json") -> Dict[str, Any]:
        data = self.finalize()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved scraping report to {file_path}")
        return data

    def generate_text_summary(self) -> str:
        m = self.metrics
        return f"""============================================================
SCRAPING EXECUTION SUMMARY
============================================================
Target:             {m.target_name}
Source:             {m.source_url} (Fixture Mode: {m.is_fixture})
Execution Window:   {m.started_at} -> {m.ended_at}
Duration:           {m.duration_seconds} seconds
Pages Attempted:    {m.pages_attempted} (Success: {m.pages_successful}, Failed: {m.pages_failed})
Records Extracted:  {m.records_extracted}
Duplicates Removed: {m.duplicates_removed}
Unique Records:     {m.records_extracted - m.duplicates_removed}
Errors Logged:      {len(m.errors)}
============================================================"""
