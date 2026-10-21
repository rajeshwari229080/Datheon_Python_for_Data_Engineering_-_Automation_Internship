# DataFlow Engineering Studio
## Autonomous Web Scraping, Data Cleaning, Relational Ingestion & Scheduled ETL Automation

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-orange.svg)](https://streamlit.io/)
[![Pytest 8.0+](https://img.shields.io/badge/pytest-passing-brightgreen.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, execution-ready internship project suite consisting of **FOUR independent Python projects** unified through a modern central web dashboard. Built for data engineering students, evaluators, and practitioners.

---

## 🌟 Project Suite Architecture

DataFlow Engineering Studio implements an end-to-end data lifecycle:

```
[1. Scraper (Requests + BS4)] ──► [2. Cleaner (Pandas + Schema)] ──► [3. Database (SQLAlchemy 2.0)]
                                                                               ▲
                                                                               │
[4. Orchestrator & Scheduler (Python Schedule + Mutex Lock + Alerts)] ─────────┘
                                       ▲
                                       │
                  [5. Central Streamlit Dashboard (app.py)]
```

---

## 📦 The Four Independent Projects

### 🕷️ Project 1 — Autonomous Web Scraper & Data Extractor
- **Tech Stack**: `Requests`, `BeautifulSoup4`
- **Features**:
  - Extracts 125+ structured records from multi-page portals or bundled offline HTML fixtures.
  - Polite crawling etiquette: descriptive User-Agent, timeouts, exponential backoff retries, rate-limiting delays, and `robots.txt` compliance.
  - Canonical record fingerprinting (SHA-256 natural key hash) to prevent duplicate records.
  - Generates telemetry and scraping reports in JSON.
- **Entry Point**: `python projects/project_1_scraper/run.py`
- **Docs**: [Project 1 README](projects/project_1_scraper/README.md)

### 🧹 Project 2 — Automated Data Cleaning & Schema Transformation
- **Tech Stack**: `Pandas`
- **Features**:
  - Non-destructive processing (raw data is preserved; outputs written to `data/processed/`).
  - Standardizes headers to `snake_case` with automated alias mapping.
  - Sanitizes whitespace, title-casing, and converts pseudo-null values (`"n/a"`, `"none"`, `"competitive"`).
  - Normalizes currencies into numeric ranges while preserving ISO currency codes (`USD`, `EUR`, `GBP`, `INR`).
  - Multi-format date parsing (ISO, European, US, relative expressions like `"3 days ago"`) into standard `YYYY-MM-DD`.
  - Enforces schema types, boundaries, and non-null constraints (`config/schema.json`).
  - Generates comprehensive Data Quality Audit Reports.
- **Entry Point**: `python projects/project_2_data_cleaning/run.py`
- **Docs**: [Project 2 README](projects/project_2_data_cleaning/README.md)

### 🗄️ Project 3 — Relational Database Auto-Ingestion & Upsert Engine
- **Tech Stack**: `SQLAlchemy 2.0` (SQLite default, PostgreSQL optional)
- **Features**:
  - Declarative schema with primary keys, indexes, and unique business key constraints (`record_hash`).
  - Idempotent upserts: re-running ingestion creates zero duplicate rows; modified records update in-place.
  - Atomic transactions with rollback isolation (tested and proven to prevent orphan rows on errors).
  - Batch processing with configurable chunk sizes.
  - Analytical query verification suite (groupings, salary statistics, top organizations).
  - Credentials kept outside code; connection URLs masked in logs.
- **Entry Point**: `python projects/project_3_database_ingestion/run.py`
- **Docs**: [Project 3 README](projects/project_3_database_ingestion/README.md)

### ⏱️ Project 4 — Scheduled End-to-End ETL Pipeline with Alerting
- **Tech Stack**: `Schedule`, `Python Logging`, `SMTP / Webhooks`
- **Features**:
  - Strict 8-stage sequence:
    `Extract -> Validate Input -> Transform -> Validate Output -> Load/Upsert -> Verify -> Report -> Notify`
  - Mutual exclusion file lock (`.pipeline.lock`) to prevent concurrent colliding runs.
  - Unique execution run IDs (`run_YYYYMMDD_HHMMSS_<uuid>`).
  - Telemetry tracking stage durations, records in/out, rotating log files (`logs/pipeline.log`).
  - Multi-channel alerting (Console default, Webhook, SMTP email) with safe offline fallbacks.
  - Dry-run mode (`--dry-run`) simulating transformations and rolling back DB writes.
  - Run-history tracking stored in SQLite table and `reports/run_history.json`.
- **Entry Point**: `python projects/project_4_scheduled_etl/run.py`
- **Docs**: [Project 4 README](projects/project_4_scheduled_etl/README.md)

---

## ⚡ Quick Start Guide

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/rajeshwari229080/Datheon_Python_for_Data_Engineering_-_Automation_Internship.git
cd Datheon_Python_for_Data_Engineering_-_Automation_Internship
pip install -r requirements.txt
```

### 2. Run the Central Streamlit Dashboard
Launch the unified interactive studio:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to access all 4 projects through a graphical interface.

### 3. Run Projects Independently via CLI

```bash
# Project 1: Web Scraper (Extracts 125 records from HTML fixtures)
python projects/project_1_scraper/run.py

# Project 2: Data Cleaning & Validation
python projects/project_2_data_cleaning/run.py

# Project 3: Relational Database Upsert Engine
python projects/project_3_database_ingestion/run.py

# Project 4: Full Scheduled ETL Pipeline (Manual execution)
python projects/project_4_scheduled_etl/run.py

# Project 4: Full Pipeline in Dry-Run Mode
python projects/project_4_scheduled_etl/run.py --dry-run

# Project 4: Scheduled Mode (Every 30 minutes)
python projects/project_4_scheduled_etl/run.py --schedule --interval 30
```

---

## 🧪 Automated Testing

Execute the comprehensive test suite across all 4 projects:
```bash
pytest tests/ -v
```
**Test Coverage Breakdown**:
- `test_scraper.py`: 8 tests (HTML parsing, missing fields, pagination, backoff, deduplication, CSV/JSON export)
- `test_cleaner.py`: 8 tests (snake_case conversion, null sanitization, currency parsing, multi-format dates, schema validation)
- `test_database.py`: 5 tests (table creation, idempotent upserts, transaction rollback, analytical queries, dry-run)
- `test_pipeline.py`: 4 tests (concurrency locking, dry-run pipeline, full live E2E pipeline, alert fallback)
- **Total**: 25 Passing Tests

---

## 📂 Project Directory Structure

```
├── app.py                             # Central Streamlit Dashboard
├── requirements.txt                   # Production dependencies
├── .gitignore                         # Git exclusion rules
├── .env.example                       # Environment template (Zero hardcoded secrets)
├── config/
│   ├── scraper_config.json            # CSS selectors, pagination & request rules
│   ├── schema.json                    # Strict dataset schema & constraints
│   └── pipeline_config.json           # Pipeline stages & scheduler parameters
├── data/
│   ├── fixtures/                      # Multi-page HTML fixtures (125 records) & dirty CSV
│   ├── raw/                           # Raw extracted datasets (CSV & JSON)
│   └── processed/                     # Cleaned, validated datasets (CSV & JSON)
├── database/
│   ├── dataflow.db                    # Populated SQLite database
│   └── verify_queries.sql             # ANSI SQL analytical verification queries
├── docs/
│   ├── architecture.md                # System design & Mermaid diagrams
│   ├── data_dictionary.md             # Complete schema column specifications
│   ├── troubleshooting.md             # Operational FAQ & recovery guide
│   └── internship_demo.md             # Evaluator demonstration sequence
├── logs/
│   └── pipeline.log                   # Rotating execution log files
├── reports/
│   ├── scraping_summary.json          # Scraper metrics & page logs
│   ├── data_quality_report.json       # Nullity rates & schema violations
│   ├── database_load_report.json      # Ingestion & table verification metrics
│   └── run_history.json               # Full pipeline execution telemetry
├── src/
│   ├── scraper/                       # Project 1 extraction core
│   ├── cleaner/                       # Project 2 normalization & schema validation
│   ├── database/                      # Project 3 SQLAlchemy models & upsert engine
│   ├── pipeline/                      # Project 4 orchestration & scheduling
│   ├── notifications/                 # Multi-channel alert dispatchers
│   └── reporting/                     # Rotating logger & HTML report builders
├── projects/
│   ├── project_1_scraper/             # Standalone runner & documentation
│   ├── project_2_data_cleaning/       # Standalone runner & documentation
│   ├── project_3_database_ingestion/  # Standalone runner & documentation
│   └── project_4_scheduled_etl/       # Standalone runner & documentation
└── tests/
    ├── conftest.py                    # Shared pytest fixtures
    ├── test_scraper.py                # Project 1 test suite
    ├── test_cleaner.py                # Project 2 test suite
    ├── test_database.py               # Project 3 test suite
    └── test_pipeline.py               # Project 4 test suite
```

---

## 🎓 Internship Evaluation Script
For step-by-step instructions on presenting this project during an internship viva or evaluation, please consult the [Internship Demonstration Guide](docs/internship_demo.md).
