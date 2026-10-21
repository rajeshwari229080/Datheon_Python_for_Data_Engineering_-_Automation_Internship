"""Unit and integration tests for Project 2: Automated Data Cleaning & Schema Transformation."""
import os
import pandas as pd
import pytest
from src.cleaner.normalizer import ColumnNormalizer
from src.cleaner.type_parsers import StringSanitizer
from src.cleaner.currency_parsers import CurrencyParser
from src.cleaner.date_parsers import DateNormalizer
from src.cleaner.validator import SchemaValidator
from src.cleaner.reporter import DataQualityReporter
from projects.project_2_data_cleaning.run import clean_dataset


def test_column_normalizer():
    normalizer = ColumnNormalizer()
    df = pd.DataFrame(columns=["Job Title", "Company Name", "Salary Range", "Job Location", "Category", "URL"])
    norm_df = normalizer.normalize_dataframe_columns(df)
    expected_cols = ["title", "organization", "salary", "location", "category", "source_url"]
    assert list(norm_df.columns) == expected_cols


def test_column_collision_resolution():
    normalizer = ColumnNormalizer()
    # Both 'detail_url' and 'url' map to 'source_url'
    df = pd.DataFrame({
        "detail_url": ["https://example.com/1", None],
        "url": [None, "https://example.com/2"]
    })
    norm_df = normalizer.normalize_dataframe_columns(df)
    assert list(norm_df.columns) == ["source_url"]
    assert norm_df["source_url"].iloc[0] == "https://example.com/1"
    assert norm_df["source_url"].iloc[1] == "https://example.com/2"


def test_string_sanitizer():
    sanitizer = StringSanitizer()
    assert sanitizer.clean_string_value("  Senior Data Engineer  ", title_case=True) == "Senior Data Engineer"
    assert sanitizer.clean_string_value("n/a") is None
    assert sanitizer.clean_string_value(" competitive ") is None
    assert sanitizer.clean_string_value("AWS Cloud Architect", title_case=True) == "AWS Cloud Architect"


def test_currency_parser_ranges():
    s_min, s_max, curr = CurrencyParser.parse_salary_range("$120,000 - $145,000")
    assert s_min == 120000.0
    assert s_max == 145000.0
    assert curr == "USD"

    s_min, s_max, curr = CurrencyParser.parse_salary_range("£85,000 - £105,000")
    assert s_min == 85000.0
    assert s_max == 105000.0
    assert curr == "GBP"

    s_min, s_max, curr = CurrencyParser.parse_salary_range("₹2,500,000 - ₹3,500,000")
    assert s_min == 2500000.0
    assert s_max == 3500000.0
    assert curr == "INR"


def test_currency_parser_k_notation():
    s_min, s_max, curr = CurrencyParser.parse_salary_range("110k - 130k USD")
    assert s_min == 110000.0
    assert s_max == 130000.0
    assert curr == "USD"


def test_date_normalizer():
    assert DateNormalizer.normalize_date("2026-10-18") == "2026-10-18"
    assert DateNormalizer.normalize_date("19/10/2026") == "2026-10-19"
    assert DateNormalizer.normalize_date("10-20-2026") == "2026-10-20"
    assert DateNormalizer.normalize_date("3 days ago") is not None
    assert DateNormalizer.normalize_date("invalid_date_xyz") is None
    assert DateNormalizer.normalize_date(None) is None


def test_schema_validator():
    schema = {
        "columns": {
            "title": {"type": "string", "required": True, "nullable": False, "max_length": 100},
            "organization": {"type": "string", "required": True, "nullable": False},
            "salary_min": {"type": "float", "required": False, "nullable": True, "min_value": 0.0}
        }
    }
    validator = SchemaValidator(schema)
    df = pd.DataFrame([
        {"title": "Valid Engineer", "organization": "Datheon", "salary_min": 100000.0},
        {"title": None, "organization": "Datheon", "salary_min": 50000.0}, # Non-nullable null
        {"title": "Underpaid", "organization": "Datheon", "salary_min": -500.0} # Below min_value
    ])
    valid_df, rejected_df, violations = validator.validate_dataframe(df)

    assert len(valid_df) == 1
    assert len(rejected_df) == 2
    assert len(violations) == 2


def test_clean_dataset_end_to_end(tmp_path):
    out_csv = str(tmp_path / "clean.csv")
    out_json = str(tmp_path / "clean.json")
    out_rep = str(tmp_path / "report.json")

    summary = clean_dataset(
        input_path="data/fixtures/dirty_jobs.csv",
        output_csv_path=out_csv,
        output_json_path=out_json,
        report_path=out_rep
    )

    assert summary["input_records"] == 30
    assert summary["output_records"] > 0
    assert summary["duplicates_removed"] > 0
    assert os.path.exists(out_csv)
    assert os.path.exists(out_json)
    assert os.path.exists(out_rep)
