"""Web scraper and extraction package."""
from src.scraper.client import PoliteHttpClient
from src.scraper.extractor import HtmlExtractor
from src.scraper.dedup import RecordDeduplicator
from src.scraper.reporter import ScrapingReporter

__all__ = ["PoliteHttpClient", "HtmlExtractor", "RecordDeduplicator", "ScrapingReporter"]
