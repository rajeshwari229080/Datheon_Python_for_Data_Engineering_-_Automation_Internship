# Troubleshooting & FAQ Guide
## DataFlow Engineering Studio

### 1. Common Operational Scenarios

#### Q1: "Could not acquire concurrency lock. Another ETL pipeline instance is running."
- **Cause**: A prior pipeline execution is actively running, or crashed abnormally leaving `.pipeline.lock` on disk.
- **Resolution**:
  1. Verify if another terminal or dashboard background process is running:
     ```bash
     ps aux | grep python  # On Linux/macOS
     Get-Process python    # On Windows PowerShell
     ```
  2. If no process is running, manually remove the stale lock file:
     ```bash
     rm .pipeline.lock     # On Linux/macOS
     Remove-Item .pipeline.lock  # On Windows PowerShell
     ```

---

#### Q2: "Database health check ping failed."
- **Cause**: The SQLite file path cannot be written, or the remote PostgreSQL host is unreachable.
- **Resolution**:
  - For SQLite: ensure the `database/` directory exists and has write permissions.
  - For PostgreSQL: verify your `DATABASE_URL` string in `.env` and verify connectivity:
    ```bash
    python -c "from src.database.engine import DatabaseEngineFactory; print(DatabaseEngineFactory().ping())"
    ```

---

#### Q3: "How do I test scraping if I have no active internet connection?"
- **Answer**: By default, Project 1 and the pipeline run in **Fixture Mode**, resolving local multi-page HTML files located in `data/fixtures/html/`. Over 125 realistic job postings are extracted completely offline without external network dependencies.
- To explicitly force live scraping, pass `--live`:
  ```bash
  python projects/project_1_scraper/run.py --live
  ```

---

#### Q4: "Where are sensitive credentials stored?"
- **Answer**: Passwords, API tokens, and SMTP credentials must **never** be hardcoded. Store them in `.env`.
- An environment template is provided at `.env.example`.
- All logging modules mask credentials automatically before outputting to logs.
