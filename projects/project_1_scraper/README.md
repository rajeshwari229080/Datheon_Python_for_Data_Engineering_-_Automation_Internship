# Project 1: Autonomous Web Scraper & Data Extractor

Part of the **DataFlow Engineering Studio** internship project suite.

## Overview
Project 1 extracts structured records from paginated web portals using `Requests` and `BeautifulSoup4`. It supports live HTTP fetching with polite crawling etiquette (User-Agent header, timeout handling, exponential backoff retries, and `robots.txt` compliance) as well as offline mode using bundled multi-page HTML fixtures for zero-network testing.

## Key Features
- **Configurable CSS Selectors**: Extract title, organization, location, salary, category, dates, and URLs via `config/scraper_config.json`.
- **Multi-Page Pagination**: Traverses multiple pages up to a user-configured limit.
- **Canonical Deduplication**: Generates deterministic SHA-256 record fingerprints based on natural keys to eliminate duplicate rows.
- **Offline HTML Fixture Support**: Bundled with 5 HTML fixture pages containing 125 realistic job records for repeatable evaluations.
- **Structured Artifact Export**: Writes raw data to `data/raw/scraped_jobs.csv` and `data/raw/scraped_jobs.json`.
- **Scraping Telemetry**: Produces an execution summary in `reports/scraping_summary.json`.

## Quick Start

### 1. Run Offline Demonstration (Default: 125 records from HTML fixtures)
```bash
python projects/project_1_scraper/run.py
```

### 2. Run with Custom Constraints
```bash
python projects/project_1_scraper/run.py --max-pages 3 --max-records 50
```

### 3. Run Live Scraping
```bash
python projects/project_1_scraper/run.py --live
```

## Output Locations
- Raw CSV: `data/raw/scraped_jobs.csv`
- Raw JSON: `data/raw/scraped_jobs.json`
- Metrics Report: `reports/scraping_summary.json`
