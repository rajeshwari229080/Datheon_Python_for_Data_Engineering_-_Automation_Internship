"""BeautifulSoup-based structured HTML extractor engine.
Extracts configurable fields and metadata with resilient handling of missing tags.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HtmlExtractor:
    """Parses raw HTML and extracts structured records according to selector config."""

    def __init__(self, selector_config: Dict[str, Any]):
        self.container_selector = selector_config.get("item_container", ".job-card")
        self.field_selectors = selector_config.get("fields", {})

    def extract_records(
        self, html_content: str, source_url: str
    ) -> List[Dict[str, Any]]:
        """Parse HTML string and extract list of structured raw dictionaries.
        
        Args:
            html_content: Raw HTML text of the page.
            source_url: The URL or fixture path from which HTML was obtained.
            
        Returns:
            List of extracted field dictionaries.
        """
        if not html_content or not html_content.strip():
            logger.warning("Empty HTML content provided for extraction.")
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        containers = soup.select(self.container_selector)
        logger.info(f"Located {len(containers)} containers with selector '{self.container_selector}'")

        extracted_records = []
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        for item in containers:
            record: Dict[str, Any] = {
                "source_url": source_url,
                "extracted_at": now_iso
            }

            for field_name, field_cfg in self.field_selectors.items():
                selector = field_cfg.get("selector")
                field_type = field_cfg.get("type", "text")
                attr_name = field_cfg.get("attribute", "href")

                if not selector:
                    continue

                element = item.select_one(selector)
                if element is None:
                    record[field_name] = None
                    continue

                if field_type == "text":
                    text_val = element.get_text(strip=True)
                    record[field_name] = text_val if text_val else None
                elif field_type == "attribute":
                    record[field_name] = element.get(attr_name, None)
                else:
                    record[field_name] = element.get_text(strip=True)

            # Only append if at least one meaningful field (e.g. title or organization) was found
            if any(record.get(k) for k in self.field_selectors.keys()):
                extracted_records.append(record)

        return extracted_records

    def find_next_page(self, html_content: str, selector: str = ".next-page") -> Optional[str]:
        """Detect next-page link in the pagination controls."""
        if not html_content:
            return None
        soup = BeautifulSoup(html_content, "html.parser")
        next_tag = soup.select_one(selector)
        if next_tag and next_tag.get("href"):
            return str(next_tag["href"]).strip()
        return None
