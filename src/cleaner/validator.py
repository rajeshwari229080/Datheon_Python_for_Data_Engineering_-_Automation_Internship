"""Schema validation and constraint checking engine.
Validates transformed tabular records against strict schema specifications.
"""
from dataclasses import dataclass, field
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SchemaViolation:
    row_index: int
    field_name: str
    violation_type: str
    message: str
    raw_value: Any


class SchemaValidator:
    """Enforces strict schema compliance on pandas DataFrames."""

    def __init__(self, schema_definition: Dict[str, Any]):
        self.schema = schema_definition
        self.columns_spec = schema_definition.get("columns", {})
        self.business_key = schema_definition.get("business_key", "record_hash")
        self.natural_keys = schema_definition.get("natural_key_fields", ["title", "organization", "location"])

    @classmethod
    def load_from_file(cls, schema_path: str) -> "SchemaValidator":
        with open(schema_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return cls(cfg)

    def compute_record_hash(self, row: pd.Series) -> str:
        """Compute stable SHA-256 natural key hash."""
        parts = []
        for col in self.natural_keys:
            val = str(row.get(col, "") or "").strip().lower()
            parts.append(val)
        raw_key = "|".join(parts)
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def validate_dataframe(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, List[SchemaViolation]]:
        """Validate entire DataFrame, separating valid records from rejected ones.
        
        Returns:
            Tuple of (valid_df, rejected_df, list_of_violations)
        """
        valid_indices = []
        rejected_indices = []
        violations: List[SchemaViolation] = []

        validated_df = df.copy()

        # Ensure business key column exists
        if self.business_key not in validated_df.columns:
            validated_df[self.business_key] = validated_df.apply(self.compute_record_hash, axis=1)

        for idx, row in validated_df.iterrows():
            row_violations = []

            for col_name, spec in self.columns_spec.items():
                is_required = spec.get("required", False)
                is_nullable = spec.get("nullable", True)
                col_type = spec.get("type", "string")
                val = row.get(col_name)

                # Check missing required columns
                if col_name not in validated_df.columns:
                    if is_required:
                        row_violations.append(
                            SchemaViolation(idx, col_name, "missing_column", f"Required column '{col_name}' missing", None)
                        )
                    continue

                # Nullability check
                if val is None or pd.isna(val) or val == "":
                    if not is_nullable:
                        row_violations.append(
                            SchemaViolation(idx, col_name, "non_nullable_null", f"Field '{col_name}' cannot be null", val)
                        )
                    continue

                # String max length check
                if col_type == "string":
                    max_len = spec.get("max_length")
                    if max_len and len(str(val)) > max_len:
                        row_violations.append(
                            SchemaViolation(idx, col_name, "max_length_exceeded", f"Length {len(str(val))} exceeds {max_len}", val)
                        )

                # Numeric boundaries check
                elif col_type in ("float", "integer"):
                    min_val = spec.get("min_value")
                    max_val = spec.get("max_value")
                    try:
                        num = float(val)
                        if min_val is not None and num < min_val:
                            row_violations.append(
                                SchemaViolation(idx, col_name, "min_value_violation", f"Value {num} is below min {min_val}", val)
                            )
                        if max_val is not None and num > max_val:
                            row_violations.append(
                                SchemaViolation(idx, col_name, "max_value_violation", f"Value {num} is above max {max_val}", val)
                            )
                    except (ValueError, TypeError):
                        row_violations.append(
                            SchemaViolation(idx, col_name, "invalid_numeric", f"Value '{val}' cannot be parsed as numeric", val)
                        )

            if row_violations:
                rejected_indices.append(idx)
                violations.extend(row_violations)
            else:
                valid_indices.append(idx)

        valid_df = validated_df.loc[valid_indices].reset_index(drop=True)
        rejected_df = validated_df.loc[rejected_indices].reset_index(drop=True) if rejected_indices else pd.DataFrame()

        return valid_df, rejected_df, violations
