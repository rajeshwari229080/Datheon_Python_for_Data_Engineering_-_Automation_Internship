"""Data quality reporting and audit trail generator.
Produces comprehensive metrics on nullity, duplicate removals, schema compliance,
and exports both machine-readable JSON and human-readable text summaries.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
import os
from typing import Any, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    input_records: int = 0
    output_records: int = 0
    duplicates_removed: int = 0
    rejected_records: int = 0
    missing_values_by_column: Dict[str, int] = field(default_factory=dict)
    missing_rates_by_column: Dict[str, float] = field(default_factory=dict)
    cleaning_actions: List[str] = field(default_factory=list)
    schema_violations: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""


class DataQualityReporter:
    """Computes dataset quality metrics and writes comprehensive audit reports."""

    def __init__(self):
        self.metrics = QualityMetrics(
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        )

    def log_action(self, action_description: str) -> None:
        self.metrics.cleaning_actions.append(action_description)

    def record_duplicates(self, count: int) -> None:
        self.metrics.duplicates_removed = count

    def analyze_nulls(self, df: pd.DataFrame) -> None:
        total = max(len(df), 1)
        for col in df.columns:
            null_count = int(df[col].isna().sum())
            self.metrics.missing_values_by_column[col] = null_count
            self.metrics.missing_rates_by_column[col] = round((null_count / total) * 100, 2)

    def record_counts(self, input_count: int, output_count: int, rejected_count: int) -> None:
        self.metrics.input_records = input_count
        self.metrics.output_records = output_count
        self.metrics.rejected_records = rejected_count

    def record_violations(self, violations: list) -> None:
        self.metrics.schema_violations = [
            {
                "row_index": v.row_index,
                "field": v.field_name,
                "violation_type": v.violation_type,
                "message": v.message,
                "raw_value": str(v.raw_value)
            }
            for v in violations
        ]

    def export_report(self, file_path: str = "reports/data_quality_report.json") -> Dict[str, Any]:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        data = asdict(self.metrics)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved data quality audit report to {file_path}")
        return data

    def generate_text_summary(self) -> str:
        m = self.metrics
        actions_str = "\n".join(f"  - {a}" for a in m.cleaning_actions) or "  - None"
        null_breakdown = "\n".join(
            f"  - {col}: {cnt} nulls ({m.missing_rates_by_column.get(col, 0.0)}%)"
            for col, cnt in m.missing_values_by_column.items()
        ) or "  - None"

        return f"""============================================================
DATA QUALITY & AUDIT REPORT
============================================================
Generated At:        {m.generated_at}
Input Records:       {m.input_records}
Output Records:      {m.output_records}
Duplicates Removed:  {m.duplicates_removed}
Rejected Records:    {m.rejected_records}
Schema Violations:   {len(m.schema_violations)}

Cleaning Actions Performed:
{actions_str}

Column Nullity Breakdown:
{null_breakdown}
============================================================"""
