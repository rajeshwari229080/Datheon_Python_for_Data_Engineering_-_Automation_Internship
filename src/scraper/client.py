"""Resilient, rate-limited, and polite HTTP client for web extraction.
Supports live web fetching with robots.txt parsing and exponential backoff,
as well as zero-network local HTML fixture resolution for reproducible testing.
"""
import logging
import os
import time
import urllib.parse
import urllib.robotparser
from typing import Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class PoliteHttpClient:
    """HTTP Client enforcing polite crawling etiquette, retries, and backoff."""

    def __init__(
        self,
        user_agent: str = "DataFlowStudioBot/1.0 (+https://dataflow.studio/bot; contact@dataflow.studio)",
        timeout_seconds: int = 10,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        rate_limit_delay_seconds: float = 0.5,
        respect_robots_txt: bool = True,
    ):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.rate_limit_delay_seconds = rate_limit_delay_seconds
        self.respect_robots_txt = respect_robots_txt
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self._robots_parsers = {}
        self._last_request_time = 0.0

    def is_allowed_by_robots(self, target_url: str) -> bool:
        """Verify whether target URL is allowed under robots.txt."""
        if not self.respect_robots_txt:
            return True
        try:
            parsed = urllib.parse.urlparse(target_url)
            if not parsed.scheme or not parsed.netloc:
                return True
            domain = f"{parsed.scheme}://{parsed.netloc}"
            if domain not in self._robots_parsers:
                robots_url = f"{domain}/robots.txt"
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(robots_url)
                try:
                    resp = self.session.get(robots_url, timeout=5)
                    if resp.status_code == 200:
                        rp.parse(resp.text.splitlines())
                    else:
                        rp.allow_all = True
                except Exception as ex:
                    logger.warning(f"Could not fetch robots.txt for {domain}: {ex}. Defaulting to allow.")
                    rp.allow_all = True
                self._robots_parsers[domain] = rp

            return self._robots_parsers[domain].can_fetch(self.user_agent, target_url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {target_url}: {e}. Proceeding conservatively.")
            return True

    def fetch_url(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Fetch remote URL with rate limiting, timeouts, and exponential backoff.
        
        Returns:
            Tuple of (success: bool, html_content: Optional[str], error_message: Optional[str])
        """
        if not self.is_allowed_by_robots(url):
            msg = f"Access denied by robots.txt policy for URL: {url}"
            logger.warning(msg)
            return False, None, msg

        # Rate-limiting enforcement
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay_seconds:
            time.sleep(self.rate_limit_delay_seconds - elapsed)

        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                self._last_request_time = time.time()
                response = self.session.get(url, timeout=self.timeout_seconds)
                response.raise_for_status()
                return True, response.text, None
            except requests.exceptions.HTTPError as he:
                status = he.response.status_code if he.response else "Unknown"
                last_error = f"HTTP {status} Error: {he}"
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed for {url}: {last_error}")
                # Do not retry 404 or 403
                if status in (404, 403, 401):
                    return False, None, last_error
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as net_err:
                last_error = f"Network/Timeout Error: {net_err}"
                logger.warning(f"Attempt {attempt}/{self.max_retries} failed for {url}: {last_error}")
            except Exception as ex:
                last_error = f"Unexpected error: {ex}"
                logger.error(f"Attempt {attempt}/{self.max_retries} unexpected failure for {url}: {last_error}")

            if attempt < self.max_retries:
                sleep_duration = self.backoff_factor ** attempt
                logger.info(f"Backing off for {sleep_duration:.2f}s before retry...")
                time.sleep(sleep_duration)

        return False, None, f"Failed after {self.max_retries} attempts. Last error: {last_error}"

    def fetch_fixture(self, file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Read local HTML fixture from disk without network access."""
        if not os.path.exists(file_path):
            msg = f"Fixture file not found: {file_path}"
            logger.error(msg)
            return False, None, msg
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return True, content, None
        except Exception as ex:
            msg = f"Failed to read fixture {file_path}: {ex}"
            logger.error(msg)
            return False, None, msg
