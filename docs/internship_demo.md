# Internship Evaluation & Technical Demonstration Guide
## DataFlow Engineering Studio

Use this script during your internship project evaluation or technical viva to systematically present and verify all deliverables.

---

### Step 1: System Overview & Dependency Verification (1 Minute)
**Objective**: Show clean environment and automated test suite.
1. Run automated test suite:
   ```bash
   pytest tests/ -v
   ```
   **Expected Evidence**: 25 tests pass across scraper, cleaner, database, and pipeline in under 5 seconds.

---

### Step 2: Project 1 Demonstration — Autonomous Web Scraper (2 Minutes)
**Objective**: Demonstrate multi-page web scraping with 100+ records and deduplication.
1. Execute standalone Project 1 runner:
   ```bash
   python projects/project_1_scraper/run.py
   ```
   **Expected Evidence**:
   - Terminal shows 5 pages attempted and 125 records extracted.
   - Shows canonical SHA-256 fingerprint deduplication.
   - Outputs created at `data/raw/scraped_jobs.csv` and `reports/scraping_summary.json`.

---

### Step 3: Project 2 Demonstration — Automated Data Cleaning (2 Minutes)
**Objective**: Demonstrate schema enforcement, snake_case conversion, currency parsing, and date normalization.
1. Execute standalone Project 2 runner against dirty dataset:
   ```bash
   python projects/project_2_data_cleaning/run.py --input data/fixtures/dirty_jobs.csv
   ```
   **Expected Evidence**:
   - Terminal prints data quality report.
   - Demonstrates 9 duplicate rows eliminated, whitespace cleaned, multi-currency values parsed into `salary_min`, `salary_max`, `currency`.
   - Rejects schema-violating rows (e.g., missing title).
   - Generates `reports/data_quality_report.json`.

---

### Step 4: Project 3 Demonstration — Relational Database & Idempotency (3 Minutes)
**Objective**: Prove idempotent upsert behavior, transaction rollback, and analytical queries.
1. Initial Ingestion:
   ```bash
   python projects/project_3_database_ingestion/run.py
   ```
   **Evidence**: 125 records inserted into `database/dataflow.db`. Duplicate count = 0.
2. Immediate Second Ingestion (Idempotency Proof):
   ```bash
   python projects/project_3_database_ingestion/run.py
   ```
   **Evidence**: `Inserted: 0`, `Unchanged: 125`. Zero duplicate records added!
3. View SQL Verification Queries:
   Show file `database/verify_queries.sql` containing ANSI SQL aggregations and duplicate checks.

---

### Step 5: Project 4 Demonstration — Scheduled End-to-End Pipeline (2 Minutes)
**Objective**: Demonstrate complete 8-stage pipeline orchestration, dry-run mode, and alerting.
1. Dry-Run Execution:
   ```bash
   python projects/project_4_scheduled_etl/run.py --dry-run
   ```
   **Evidence**: All 8 stages run successfully; status flagged as `DRY_RUN`; database writes rolled back safely.
2. Manual Live Execution:
   ```bash
   python projects/project_4_scheduled_etl/run.py
   ```
   **Evidence**: Console shows formatted alert banner, run history saved to `reports/run_history.json`.

---

### Step 6: Interactive Dashboard Demonstration (2 Minutes)
**Objective**: Present the central Streamlit dashboard.
1. Launch dashboard:
   ```bash
   streamlit run app.py
   ```
2. Walk through:
   - **Studio Overview**: Architecture diagram and project cards.
   - **Project 1**: View extracted records and download raw CSV/JSON.
   - **Project 2**: Review data quality metrics and before/after comparisons.
   - **Project 3**: Analytical query explorer (filtering jobs by salary & category) + Rollback test button.
   - **Project 4**: Scheduler controller (Start/Stop background scheduling) and historical run metrics table.
