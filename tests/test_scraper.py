"""Unit and integration tests for Project 1: Autonomous Web Scraper."""
import os
import pytest
from src.scraper.client import PoliteHttpClient
from src.scraper.extractor import HtmlExtractor
from src.scraper.dedup import RecordDeduplicator, export_records_to_csv, export_records_to_json
from src.scraper.reporter import ScrapingReporter
from projects.project_1_scraper.run import run_scraper


def test_extractor_parses_job_cards(sample_job_html, selector_config):
    extractor = HtmlExtractor(selector_config)
    records = extractor.extract_records(sample_job_html, source_url="https://example.com/test")

    assert len(records) == 2
    r1 = records[0]
    assert r1["title"] == "Senior Data Engineer"
    assert r1["organization"] == "Datheon Systems"
    assert r1["location"] == "Remote"
    assert r1["salary"] == "$140,000 - $160,000"
    assert r1["posted_date"] == "2026-10-18"
    assert r1["detail_url"] == "/jobs/01"

    r2 = records[1]
    assert r2["title"] == "Junior Analyst"
    assert r2["salary"] is None  # Missing/empty element handled cleanly


def test_extractor_finds_next_page(sample_job_html, selector_config):
    extractor = HtmlExtractor(selector_config)
    next_page = extractor.find_next_page(sample_job_html, selector=".next-page")
    assert next_page == "/jobs?page=2"


def test_extractor_empty_html(selector_config):
    extractor = HtmlExtractor(selector_config)
    records = extractor.extract_records("", source_url="https://example.com/empty")
    assert records == []


def test_deduplicator_filters_duplicates():
    dedup = RecordDeduplicator(key_fields=["title", "organization", "location"])
    records = [
        {"title": "Data Engineer", "organization": "Datheon", "location": "Remote"},
        {"title": "data engineer", "organization": "Datheon ", "location": " remote"}, # duplicate (case/whitespace)
        {"title": "Cloud Architect", "organization": "Apex", "location": "Austin, TX"}
    ]
    unique, dup_count = dedup.filter_duplicates(records)
    assert len(unique) == 2
    assert dup_count == 1
    assert "record_hash" in unique[0]
    assert len(unique[0]["record_hash"]) == 64  # SHA-256 length


def test_polite_http_client_fixture_reading():
    client = PoliteHttpClient()
    fixture_path = os.path.join("data", "fixtures", "html", "jobs_page_1.html")
    success, content, err = client.fetch_fixture(fixture_path)
    assert success is True
    assert "TechCareers" in content
    assert err is None


def test_polite_http_client_missing_fixture():
    client = PoliteHttpClient()
    success, content, err = client.fetch_fixture("non_existent_file.html")
    assert success is False
    assert content is None
    assert "not found" in err.lower()


def test_reporter_metrics_and_summary():
    reporter = ScrapingReporter(target_name="Test Target", source_url="https://test.com", is_fixture=True)
    reporter.record_page_attempt()
    reporter.record_page_success(15)
    reporter.record_duplicates(2)
    summary = reporter.finalize()

    assert summary["target_name"] == "Test Target"
    assert summary["pages_attempted"] == 1
    assert summary["pages_successful"] == 1
    assert summary["records_extracted"] == 15
    assert summary["duplicates_removed"] == 2
    assert summary["duration_seconds"] >= 0.0


def test_full_offline_scraper_execution(tmp_path):
    csv_out = str(tmp_path / "test_jobs.csv")
    json_out = str(tmp_path / "test_jobs.json")

    summary = run_scraper(
        config_path="config/scraper_config.json",
        force_live=False,
        override_max_pages=5,
        custom_output_csv=csv_out,
        custom_output_json=json_out
    )

    # Acceptance criteria: At least 100 records extracted from offline fixture
    assert summary["records_extracted"] >= 100
    assert summary["pages_successful"] == 5
    assert os.path.exists(csv_out)
    assert os.path.exists(json_out)
