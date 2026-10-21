"""Standalone entry point for Project 1: Autonomous Web Scraper & Data Extractor.
Can be executed directly via:
    python projects/project_1_scraper/run.py
"""
import argparse
import json
import logging
import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.scraper.client import PoliteHttpClient
from src.scraper.extractor import HtmlExtractor
from src.scraper.dedup import RecordDeduplicator, export_records_to_csv, export_records_to_json
from src.scraper.reporter import ScrapingReporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("project_1_scraper")


def run_scraper(
    config_path: str = "config/scraper_config.json",
    force_live: bool = False,
    override_max_pages: int = None,
    override_max_records: int = None,
    custom_output_csv: str = None,
    custom_output_json: str = None,
) -> dict:
    """Execute scraping extraction workflow according to configuration."""
    abs_config_path = os.path.join(REPO_ROOT, config_path)
    if not os.path.exists(abs_config_path):
        raise FileNotFoundError(f"Configuration file not found: {abs_config_path}")

    with open(abs_config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    target_name = cfg.get("target_name", "TechCareers Portal")
    base_url = cfg.get("base_url", "https://example.com/jobs")
    fixture_mode = cfg.get("fixture_mode", True) and not force_live
    fixture_dir = os.path.join(REPO_ROOT, cfg.get("fixture_dir", "data/fixtures/html"))

    req_cfg = cfg.get("request_settings", {})
    client = PoliteHttpClient(
        user_agent=req_cfg.get("user_agent", "DataFlowStudioBot/1.0"),
        timeout_seconds=req_cfg.get("timeout_seconds", 10),
        max_retries=req_cfg.get("max_retries", 3),
        backoff_factor=req_cfg.get("backoff_factor", 1.5),
        rate_limit_delay_seconds=req_cfg.get("rate_limit_delay_seconds", 0.5),
    )

    extractor = HtmlExtractor(cfg.get("selectors", {}))
    deduplicator = RecordDeduplicator(key_fields=["title", "organization", "location"])
    reporter = ScrapingReporter(target_name, base_url, is_fixture=fixture_mode)

    pag_cfg = cfg.get("pagination", {})
    max_pages = override_max_pages or pag_cfg.get("max_pages", 5)
    max_records = override_max_records or pag_cfg.get("max_records", 150)
    start_page = pag_cfg.get("start_page", 1)

    all_raw_records = []
    logger.info(f"Starting Project 1 Scraper: {target_name} (Fixture mode: {fixture_mode})")

    for page_idx in range(start_page, start_page + max_pages):
        reporter.record_page_attempt()

        if fixture_mode:
            page_filename = f"jobs_page_{page_idx}.html"
            fixture_path = os.path.join(fixture_dir, page_filename)
            logger.info(f"Loading local HTML fixture: {fixture_path}")
            success, html, err = client.fetch_fixture(fixture_path)
            current_url = f"file:///{fixture_path}"
        else:
            page_url = f"{base_url}?page={page_idx}"
            logger.info(f"Fetching remote page {page_idx}: {page_url}")
            success, html, err = client.fetch_url(page_url)
            current_url = page_url

        if not success:
            logger.warning(f"Failed to fetch page {page_idx}: {err}")
            reporter.record_page_failure(err or "Fetch failed")
            if fixture_mode and not os.path.exists(fixture_path):
                # End of fixture pages
                break
            continue

        records = extractor.extract_records(html, source_url=current_url)
        reporter.record_page_success(len(records))
        all_raw_records.extend(records)
        logger.info(f"Page {page_idx} extracted {len(records)} records.")

        if len(all_raw_records) >= max_records:
            logger.info(f"Reached record limit target ({max_records}). Stopping pagination.")
            break

    # Apply canonical deduplication
    unique_records, dup_count = deduplicator.filter_duplicates(all_raw_records)
    reporter.record_duplicates(dup_count)
    logger.info(f"Deduplication complete. Extracted: {len(all_raw_records)}, Unique: {len(unique_records)}, Duplicates: {dup_count}")

    # Export paths
    out_cfg = cfg.get("output", {})
    csv_path = custom_output_csv or os.path.join(REPO_ROOT, out_cfg.get("raw_csv_path", "data/raw/scraped_jobs.csv"))
    json_path = custom_output_json or os.path.join(REPO_ROOT, out_cfg.get("raw_json_path", "data/raw/scraped_jobs.json"))
    report_path = os.path.join(REPO_ROOT, out_cfg.get("report_path", "reports/scraping_summary.json"))

    export_records_to_csv(unique_records, csv_path)
    export_records_to_json(unique_records, json_path)

    reporter.set_output_files({
        "csv": csv_path,
        "json": json_path,
        "report": report_path
    })
    summary = reporter.export_report(report_path)
    print(reporter.generate_text_summary())
    return summary


def main():
    parser = argparse.ArgumentParser(description="DataFlow Project 1: Autonomous Web Scraper")
    parser.add_argument("--config", default="config/scraper_config.json", help="Path to scraper configuration")
    parser.add_argument("--live", action="store_true", help="Force live web scraping instead of offline fixture")
    parser.add_argument("--max-pages", type=int, help="Override maximum pages to scrape")
    parser.add_argument("--max-records", type=int, help="Override maximum records to scrape")
    parser.add_argument("--csv", help="Override CSV output path")
    parser.add_argument("--json", help="Override JSON output path")
    args = parser.parse_args()

    try:
        summary = run_scraper(
            config_path=args.config,
            force_live=args.live,
            override_max_pages=args.max_pages,
            override_max_records=args.max_records,
            custom_output_csv=args.csv,
            custom_output_json=args.json
        )
        if summary.get("records_extracted", 0) == 0 and summary.get("pages_failed", 0) > 0:
            sys.exit(1)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal scraper error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
