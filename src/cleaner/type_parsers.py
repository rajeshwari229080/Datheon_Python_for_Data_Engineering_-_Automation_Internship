"""String sanitization, whitespace stripping, and null value handling.
Converts pseudo-null strings to proper nulls and normalizes text casing.
"""
import re
from typing import Any, List, Optional
import numpy as np
import pandas as pd


class StringSanitizer:
    """Sanitizes text fields, collapses whitespace, and handles missing/blank values."""

    NULL_STRINGS = {
        "", " ", "  ", "n/a", "na", "null", "none", "nan", "nil", "unknown",
        "-", "--", "undefined", "<empty>", "not specified", "competitive"
    }

    @classmethod
    def clean_string_value(cls, val: Any, title_case: bool = False) -> Optional[str]:
        """Sanitize single text cell value."""
        if val is None or pd.isna(val):
            return None
        text = str(val).strip()
        # Collapse multiple internal whitespaces/tabs
        text = re.sub(r"\s+", " ", text)
        if text.lower() in cls.NULL_STRINGS:
            return None
        if title_case and len(text) > 1:
            words = text.split(" ")
            cased = []
            for w in words:
                if w.isupper() and len(w) in (2, 3, 4):
                    cased.append(w)
                else:
                    cased.append(w.capitalize())
            return " ".join(cased)
        return text

    def sanitize_dataframe(
        self,
        df: pd.DataFrame,
        text_columns: Optional[List[str]] = None,
        title_case_columns: Optional[List[str]] = None,
        fill_defaults: Optional[dict] = None
    ) -> pd.DataFrame:
        """Apply text sanitization and null standardization across specified columns."""
        cleaned_df = df.copy()
        if text_columns:
            target_cols = [c for c in text_columns if c in cleaned_df.columns]
        else:
            target_cols = list(cleaned_df.select_dtypes(include=["object"]).columns)

        title_case_cols = set(title_case_columns or ["title", "organization", "location", "category"])

        for col in target_cols:
            should_title_case = col in title_case_cols
            series = cleaned_df[col]
            if isinstance(series, pd.Series):
                cleaned_df[col] = series.apply(
                    lambda v: self.clean_string_value(v, title_case=should_title_case)
                )

        if fill_defaults:
            for col, default_val in fill_defaults.items():
                if col in cleaned_df.columns:
                    cleaned_df[col] = cleaned_df[col].fillna(default_val)

        return cleaned_df
