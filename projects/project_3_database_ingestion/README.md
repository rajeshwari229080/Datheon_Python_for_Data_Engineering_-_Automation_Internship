# Project 3: Relational Database Auto-Ingestion & Upsert Engine

Part of the **DataFlow Engineering Studio** internship project suite.

## Overview
Project 3 loads validated, structured data into a relational database using `SQLAlchemy 2.0`. It provides idempotent upsert behavior (inserting new records and updating existing records in-place without creating duplicates), transaction management with rollback safety, batch processing, and query verification scripts.

## Key Features
- **SQLAlchemy 2.0 Declarative Models**: Full relational schema with indexes, primary keys, and unique business key constraints (`record_hash`).
- **SQLite by Default / PostgreSQL Optional**: Runs out-of-the-box locally with zero setup, with PostgreSQL connectivity via `DATABASE_URL`.
- **Idempotent Batch Upserts**: Safe against repeated runs; updates non-key attributes without row duplication.
- **Atomic Transactions & Safe Rollbacks**: Rollback protection prevents orphaned partial rows upon failures.
- **Analytical Query Verifier**: Includes built-in aggregation, filtering, duplicate audits, and sorting queries.
- **Audit Reporting**: Writes ingestion metrics and database state to `reports/database_load_report.json`.

## Quick Start

### 1. Ingest Cleaned Jobs Dataset
```bash
python projects/project_3_database_ingestion/run.py
```

### 2. Test Idempotency (Re-run same dataset)
```bash
python projects/project_3_database_ingestion/run.py
# Verify that Inserted = 0 and Unchanged = 125, with 0 duplicates!
```

### 3. Dry-Run Mode (Simulate without committing writes)
```bash
python projects/project_3_database_ingestion/run.py --dry-run
```

## SQL Query Verification
Raw ANSI SQL verification scripts are available at `database/verify_queries.sql`.
