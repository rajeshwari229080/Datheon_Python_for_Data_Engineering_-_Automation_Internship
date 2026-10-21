"""Deduplication and artifact export engine for scraped records.
Computes deterministic SHA-256 fingerprints to eliminate duplicate records
and exports clean CSV and JSON files.
"""
import csv
import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class RecordDeduplicator:
    """Detects and suppresses duplicate records using canonical fingerprints."""

    def __init__(self, key_fields: List[str] = None):
        self.key_fields = key_fields or ["title", "organization", "location"]
        self.seen_fingerprints: Set[str] = set()

    def compute_fingerprint(self, record: Dict[str, Any]) -> str:
        """Generate deterministic SHA-256 hash from normalized natural key fields."""
        tokens = []
        for field in self.key_fields:
            val = str(record.get(field, "") or "").strip().lower()
            tokens.append(val)
        raw_key = "|".join(tokens)
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def filter_duplicates(
        self, records: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Filter incoming records against seen fingerprints.
        
        Returns:
            Tuple of (unique_records, duplicate_count)
        """
        unique_records = []
        duplicates = 0

        for r in records:
            fp = self.compute_fingerprint(r)
            if fp in self.seen_fingerprints:
                duplicates += 1
                logger.debug(f"Duplicate record suppressed: {r.get('title')} at {r.get('organization')}")
            else:
                self.seen_fingerprints.add(fp)
                r_with_fp = dict(r)
                r_with_fp["record_hash"] = fp
                unique_records.append(r_with_fp)

        return unique_records, duplicates


def export_records_to_csv(records: List[Dict[str, Any]], file_path: str) -> None:
    """Write records to CSV with UTF-8 encoding and standard headers."""
    if not records:
        logger.warning(f"No records to export to CSV: {file_path}")
        return
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    fieldnames = list(records[0].keys())
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Exported {len(records)} records to CSV: {file_path}")


def export_records_to_json(records: List[Dict[str, Any]], file_path: str) -> None:
    """Write records to formatted JSON with UTF-8 encoding."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    logger.info(f"Exported {len(records)} records to JSON: {file_path}")
