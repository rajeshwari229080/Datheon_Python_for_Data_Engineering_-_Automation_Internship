"""Standalone entry point for Project 2: Automated Data Cleaning & Schema Transformation.
Can be executed directly via:
    python projects/project_2_data_cleaning/run.py
"""
import argparse
import json
import logging
import os
import sys
from typing import Optional
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.cleaner.normalizer import ColumnNormalizer
from src.cleaner.type_parsers import StringSanitizer
from src.cleaner.currency_parsers import CurrencyParser
from src.cleaner.date_parsers import DateNormalizer
from src.cleaner.validator import SchemaValidator
from src.cleaner.reporter import DataQualityReporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("project_2_data_cleaning")


def clean_dataset(
    input_path: Optional[str] = None,
    schema_path: str = "config/schema.json",
    output_csv_path: str = "data/processed/cleaned_jobs.csv",
    output_json_path: str = "data/processed/cleaned_jobs.json",
    report_path: str = "reports/data_quality_report.json"
) -> dict:
    """Execute full data cleaning, normalization, and validation workflow."""
    reporter = DataQualityReporter()

    # Determine input path
    target_input = input_path
    if not target_input or not os.path.exists(os.path.join(REPO_ROOT, target_input)):
        default_raw = os.path.join(REPO_ROOT, "data/raw/scraped_jobs.csv")
        fixture_raw = os.path.join(REPO_ROOT, "data/fixtures/dirty_jobs.csv")
        target_input = default_raw if os.path.exists(default_raw) else fixture_raw

    abs_input = os.path.join(REPO_ROOT, target_input) if not os.path.isabs(target_input) else target_input
    logger.info(f"Loading input dataset from: {abs_input}")

    if abs_input.endswith(".json"):
        df = pd.read_json(abs_input)
    else:
        df = pd.read_csv(abs_input)

    input_count = len(df)
    reporter.log_action(f"Loaded {input_count} records from {os.path.basename(abs_input)}")

    # 1. Normalize Column Names to snake_case
    normalizer = ColumnNormalizer()
    df = normalizer.normalize_dataframe_columns(df)
    reporter.log_action(f"Normalized column headers to snake_case: {list(df.columns)}")

    # 2. Text sanitization and whitespace cleanup
    sanitizer = StringSanitizer()
    df = sanitizer.sanitize_dataframe(
        df,
        title_case_columns=["title", "organization", "location", "category"],
        fill_defaults={"location": "Remote", "category": "Engineering"}
    )
    reporter.log_action("Sanitized whitespace, standardized title-casing, applied defaults for location/category")

    # 3. Deduplication on natural keys (title + organization + location)
    initial_len = len(df)
    # Generate temporary lowercase tokens for stable deduplication
    dedup_series = df.apply(
        lambda r: f"{str(r.get('title','')).strip().lower()}|{str(r.get('organization','')).strip().lower()}|{str(r.get('location','')).strip().lower()}",
        axis=1
    )
    df = df.loc[~dedup_series.duplicated()].reset_index(drop=True)
    dup_removed = initial_len - len(df)
    reporter.record_duplicates(dup_removed)
    if dup_removed > 0:
        reporter.log_action(f"Detected and eliminated {dup_removed} duplicate records")

    # 4. Currency and Salary Range Normalization
    salary_mins = []
    salary_maxs = []
    currencies = []
    for val in df.get("salary", [None] * len(df)):
        s_min, s_max, curr = CurrencyParser.parse_salary_range(val)
        salary_mins.append(s_min)
        salary_maxs.append(s_max)
        currencies.append(curr or "USD")

    df["salary_min"] = salary_mins
    df["salary_max"] = salary_maxs
    df["currency"] = currencies
    reporter.log_action("Parsed salary ranges into numeric salary_min, salary_max, and preserved currency codes")

    # 5. Date Normalization to ISO-8601
    if "posted_date" in df.columns:
        df["posted_date"] = df["posted_date"].apply(DateNormalizer.normalize_date)
        reporter.log_action("Normalized heterogeneous dates into standard ISO-8601 YYYY-MM-DD")

    # Ensure source_url and extracted_at exist
    if "source_url" not in df.columns:
        df["source_url"] = "https://example.com/jobs/default"
    if "extracted_at" not in df.columns:
        df["extracted_at"] = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M:%S")

    # 6. Schema Validation & Constraint Checking
    abs_schema = os.path.join(REPO_ROOT, schema_path) if not os.path.isabs(schema_path) else schema_path
    validator = SchemaValidator.load_from_file(abs_schema)
    valid_df, rejected_df, violations = validator.validate_dataframe(df)

    reporter.record_violations(violations)
    reporter.record_counts(input_count, len(valid_df), len(rejected_df))
    reporter.analyze_nulls(valid_df)
    reporter.log_action(f"Schema validated: {len(valid_df)} records approved, {len(rejected_df)} records rejected")

    # 7. Export Outputs
    abs_out_csv = os.path.join(REPO_ROOT, output_csv_path) if not os.path.isabs(output_csv_path) else output_csv_path
    abs_out_json = os.path.join(REPO_ROOT, output_json_path) if not os.path.isabs(output_json_path) else output_json_path
    abs_report = os.path.join(REPO_ROOT, report_path) if not os.path.isabs(report_path) else report_path

    os.makedirs(os.path.dirname(abs_out_csv), exist_ok=True)
    os.makedirs(os.path.dirname(abs_out_json), exist_ok=True)

    # Order columns nicely according to schema
    schema_cols = [c for c in validator.columns_spec.keys() if c in valid_df.columns]
    ordered_df = valid_df[schema_cols]

    ordered_df.to_csv(abs_out_csv, index=False)
    ordered_df.to_json(abs_out_json, orient="records", indent=2)
    summary = reporter.export_report(abs_report)

    print(reporter.generate_text_summary())
    return summary


def main():
    parser = argparse.ArgumentParser(description="DataFlow Project 2: Automated Data Cleaning & Schema Transformation")
    parser.add_argument("--input", help="Path to input raw CSV/JSON file")
    parser.add_argument("--schema", default="config/schema.json", help="Path to schema definition")
    parser.add_argument("--csv", default="data/processed/cleaned_jobs.csv", help="Path to cleaned output CSV")
    parser.add_argument("--json", default="data/processed/cleaned_jobs.json", help="Path to cleaned output JSON")
    parser.add_argument("--report", default="reports/data_quality_report.json", help="Path to quality report")
    args = parser.parse_args()

    try:
        summary = clean_dataset(
            input_path=args.input,
            schema_path=args.schema,
            output_csv_path=args.csv,
            output_json_path=args.json,
            report_path=args.report
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal data cleaning error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
