"""Shared pytest fixtures and test configurations."""
import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


@pytest.fixture
def sample_job_html():
    return """
    <html>
    <body>
        <div class="job-card" id="job-01">
            <h2 class="job-title"><a class="job-link" href="/jobs/01">Senior Data Engineer</a></h2>
            <div class="company-name">Datheon Systems</div>
            <div class="job-location">Remote</div>
            <div class="job-category">Data Engineering</div>
            <span class="job-salary">$140,000 - $160,000</span>
            <div class="posted-date">2026-10-18</div>
        </div>
        <div class="job-card" id="job-02">
            <h2 class="job-title"><a class="job-link" href="/jobs/02">Junior Analyst</a></h2>
            <div class="company-name">Apex Labs</div>
            <div class="job-location">New York, NY</div>
            <div class="job-category">Analytics</div>
            <span class="job-salary empty"></span>
            <div class="posted-date">2 days ago</div>
        </div>
        <a class="next-page" href="/jobs?page=2">Next</a>
    </body>
    </html>
    """


@pytest.fixture
def selector_config():
    return {
        "item_container": ".job-card",
        "fields": {
            "title": {"selector": ".job-title", "type": "text"},
            "organization": {"selector": ".company-name", "type": "text"},
            "location": {"selector": ".job-location", "type": "text"},
            "salary": {"selector": ".job-salary", "type": "text"},
            "category": {"selector": ".job-category", "type": "text"},
            "posted_date": {"selector": ".posted-date", "type": "text"},
            "detail_url": {"selector": "a.job-link", "type": "attribute", "attribute": "href"}
        }
    }
