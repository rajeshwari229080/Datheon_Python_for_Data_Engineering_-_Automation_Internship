# Data Dictionary & Schema Specification
## DataFlow Engineering Studio

### Table: `job_postings`
The primary relational entity storing validated, normalized job market opportunities.

| Column Name | SQL Type | Nullable | Key / Index | Description & Rules |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | No | Primary Key | Autoincrementing relational identifier. |
| `record_hash` | `VARCHAR(64)` | No | Unique, Index | SHA-256 fingerprint generated from `lower(title)\|lower(organization)\|lower(location)`. |
| `title` | `VARCHAR(255)` | No | Indexed | Standardized job role title. Title-cased with technical acronym preservation. |
| `organization` | `VARCHAR(255)` | No | Indexed | Standardized hiring company name. |
| `location` | `VARCHAR(255)` | Yes | Composite Index | Work location (City/State/Country or 'Remote'). Defaults to 'Remote'. |
| `category` | `VARCHAR(100)` | Yes | Composite Index | Job industry specialization. Defaults to 'Engineering'. |
| `salary_min` | `FLOAT` | Yes | - | Minimum annual compensation magnitude parsed as float. |
| `salary_max` | `FLOAT` | Yes | - | Maximum annual compensation magnitude parsed as float. |
| `currency` | `VARCHAR(10)` | Yes | - | Preserved ISO currency code (`USD`, `EUR`, `GBP`, `INR`, `CAD`). Defaults to `USD`. |
| `posted_date` | `DATE` | Yes | - | Normalized ISO-8601 posting date (`YYYY-MM-DD`). |
| `source_url` | `VARCHAR(1024)`| No | - | Source portal URL or canonical identifier. |
| `extracted_at` | `DATETIME` | No | - | UTC timestamp when raw record was acquired. |
| `created_at` | `DATETIME` | No | - | UTC timestamp when row was first inserted into database. |
| `updated_at` | `DATETIME` | No | - | UTC timestamp when row was last updated in place. |

---

### Table: `etl_run_history`
Audit and telemetry entity tracking every execution of the end-to-end pipeline.

| Column Name | SQL Type | Nullable | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | No | Primary Key | Autoincrementing record ID. |
| `run_id` | `VARCHAR(64)` | No | Unique, Index | Unique execution identifier: `run_YYYYMMDD_HHMMSS_<uuid>`. |
| `pipeline_name`| `VARCHAR(100)`| No | - | Name of pipeline definition. |
| `status` | `VARCHAR(20)` | No | Indexed | Final run state: `SUCCESS`, `FAILED`, `DRY_RUN`, `PARTIAL`. |
| `started_at` | `DATETIME` | No | - | UTC execution start timestamp. |
| `ended_at` | `DATETIME` | Yes | - | UTC execution completion timestamp. |
| `duration_seconds`| `FLOAT` | Yes | - | Total runtime in seconds. |
| `records_extracted`| `INTEGER` | Yes | - | Total raw records parsed by scraper. |
| `records_cleaned`| `INTEGER` | Yes | - | Total records surviving schema validation. |
| `records_inserted`| `INTEGER` | Yes | - | New rows inserted into database. |
| `records_updated` | `INTEGER` | Yes | - | Existing rows updated in place. |
| `records_unchanged`| `INTEGER`| Yes | - | Duplicate rows identified with zero field diffs. |
| `records_failed` | `INTEGER` | Yes | - | Rows rejected due to database or transaction errors. |
| `error_message` | `TEXT` | Yes | - | Diagnostic error message and exception trace if failed. |
