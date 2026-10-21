# Project 2: Automated Data Cleaning & Schema Transformation

Part of the **DataFlow Engineering Studio** internship project suite.

## Overview
Project 2 transforms messy, heterogeneous datasets into validated, production-ready tabular data. It normalizes headers to snake_case, cleans whitespace and casing, parses currency amounts and preserved codes, normalizes dates to ISO-8601, and enforces strict schema constraints defined in `config/schema.json`.

## Key Features
- **Header Normalization**: Converts headers into `snake_case` with automated alias mapping.
- **Whitespace & Null Sanitization**: Detects empty or pseudo-null values (`"N/A"`, `"none"`, `"competitive"`) and replaces them with standard nulls.
- **Numeric & Currency Extraction**: Decouples currency symbols (`USD`, `EUR`, `GBP`, `INR`) and parses minimum/maximum salaries without speculative exchange rate conversions.
- **Multi-Format Date Parsing**: Normalizes ISO, European, US, and relative date expressions (`"3 days ago"`) into standard `YYYY-MM-DD`.
- **Schema Validation**: Enforces column types, non-null constraints, and boundaries against `config/schema.json`.
- **Quality Audit Trail**: Produces `reports/data_quality_report.json` with nullity rates, duplicate counts, and schema violations.

## Quick Start

### 1. Clean Scraped Dataset
```bash
python projects/project_2_data_cleaning/run.py
```

### 2. Clean Custom or Dirty Dataset
```bash
python projects/project_2_data_cleaning/run.py --input data/fixtures/dirty_jobs.csv
```

## Output Locations
- Cleaned CSV: `data/processed/cleaned_jobs.csv`
- Cleaned JSON: `data/processed/cleaned_jobs.json`
- Quality Report: `reports/data_quality_report.json`
