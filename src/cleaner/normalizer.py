"""Column normalization and snake_case transformation engine.
Maps arbitrary and messy header names into standardized snake_case schema columns.
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
        """Convert arbitrary text string to clean snake_case."""
        if not text:
            return ""
        # Replace non-alphanumeric with space
        cleaned = re.sub(r"[^\w\s]", " ", text)
        # Split on uppercase transitions (e.g. CamelCase -> camel_case)
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", cleaned)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        # Replace whitespace or hyphens with single underscore
        snake = re.sub(r"[\s\-]+", "_", s2).strip("_").lower()
        return snake

    def normalize_dataframe_columns(
        self, df: pd.DataFrame, custom_aliases: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """Normalize all columns of a pandas DataFrame to snake_case and mapped aliases."""
        alias_map = dict(self.STANDARD_ALIASES)
        if custom_aliases:
            alias_map.update(custom_aliases)

        renamed_cols = {}
        for col in df.columns:
            snake_col = self.to_snake_case(str(col))
            final_col = alias_map.get(snake_col, snake_col)
            renamed_cols[col] = final_col

        return df.rename(columns=renamed_cols)
