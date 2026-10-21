"""Column normalization and snake_case transformation engine.
Maps arbitrary and messy header names into standardized snake_case schema columns
and handles duplicate column collisions cleanly.
"""
import re
from typing import Dict, List, Optional
import pandas as pd


class ColumnNormalizer:
    """Normalizes DataFrame column names to consistent snake_case format with alias mapping."""

    STANDARD_ALIASES: Dict[str, str] = {
        "job_title": "title",
        "job_name": "title",
        "position": "title",
        "role": "title",
        "company_name": "organization",
        "company": "organization",
        "employer": "organization",
        "seller": "organization",
        "hiring_organization": "organization",
        "job_location": "location",
        "loc": "location",
        "city": "location",
        "work_location": "location",
        "job_category": "category",
        "cat": "category",
        "domain": "category",
        "salary_range": "salary",
        "pay": "salary",
        "compensation": "salary",
        "wage": "salary",
        "posted_date": "posted_date",
        "date_posted": "posted_date",
        "date": "posted_date",
        "publication_date": "posted_date",
        "detail_url": "source_url",
        "url": "source_url",
        "link": "source_url",
        "job_link": "source_url"
    }

    @staticmethod
    def to_snake_case(text: str) -> str:
        """Convert arbitrary text string to clean snake_case with single underscores."""
        if not text:
            return ""
        # Clean non-alphanumeric characters
        s = re.sub(r"[^\w\s]", " ", str(text))
        # Insert space before camelCase transitions
        s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
        # Collapse multiple spaces and underscores
        s = re.sub(r"[\s_]+", "_", s).strip("_").lower()
        return s

    def normalize_dataframe_columns(
        self, df: pd.DataFrame, custom_aliases: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """Normalize all columns of a pandas DataFrame to snake_case and mapped aliases,
        resolving duplicate column collisions by coalescing or dropping duplicates."""
        alias_map = dict(self.STANDARD_ALIASES)
        if custom_aliases:
            alias_map.update(custom_aliases)

        new_cols = []
        for col in df.columns:
            snake_col = self.to_snake_case(str(col))
            final_col = alias_map.get(snake_col, snake_col)
            new_cols.append(final_col)

        # Build a new DataFrame with uniquely named columns, coalescing if duplicate
        out_df = pd.DataFrame(index=df.index)
        for orig_col, target_col in zip(df.columns, new_cols):
            orig_series = df[orig_col]
            if isinstance(orig_series, pd.DataFrame):
                orig_series = orig_series.iloc[:, 0]

            if target_col in out_df.columns:
                out_df[target_col] = out_df[target_col].combine_first(orig_series)
            else:
                out_df[target_col] = orig_series

        return out_df
