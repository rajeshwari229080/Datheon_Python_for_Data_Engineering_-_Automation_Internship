"""Deterministic fixture generator for DataFlow Engineering Studio.
Generates 5 multi-page HTML fixtures with 125 realistic job records,
plus a sample messy CSV dataset with realistic real-world defects.
"""
import os
import csv
from datetime import datetime

TITLES = [
    "Senior Data Engineer", "Data Platform Architect", "Lead Python Developer",
    "ETL Pipeline Specialist", "Backend Software Engineer", "Machine Learning Engineer",
    "Analytics Engineer", "Big Data Developer", "Cloud Infrastructure Engineer",
    "DevOps & Automation Engineer", "Full Stack Python Developer", "Database Administrator",
    "BI Developer", "Data Systems Architect", "Site Reliability Engineer",
    "AI Solutions Engineer", "Data Warehouse Engineer", "MLOps Specialist",
    "Data Quality Analyst", "Stream Processing Engineer", "Software Architect",
    "Principal Data Engineer", "API Integrations Engineer", "Platform Reliability Engineer",
    "Data Governance Specialist"
]

COMPANIES = [
    "Datheon Systems", "Apex Data Labs", "CloudScale Technologies",
    "Nexus Analytics", "CyberPulse Corp", "Quantum Stream Inc",
    "Acuity Logic", "Vanguard Dataworks", "Synthetix AI",
    "Velocity Cloud", "Hyperion Dynamics", "InfraCore Solutions",
    "Zenith Technologies", "Krypton Labs", "Pinnacle Systems"
]

LOCATIONS = [
    "Remote", "New York, NY", "San Francisco, CA", "Austin, TX",
    "Seattle, WA", "Chicago, IL", "Boston, MA", "Denver, CO",
    "Atlanta, GA", "London, UK", "Toronto, Canada", "Bangalore, India"
]

CATEGORIES = [
    "Data Engineering", "Backend Engineering", "Cloud & DevOps",
    "Data Science & AI", "Database Administration", "Software Architecture"
]

SALARIES = [
    "$120,000 - $145,000", "$135,000 - $160,000", "$150,000 - $180,000",
    "USD 110,000 - 130,000", "$95,000 - $115,000", "£85,000 - £105,000",
    "€90,000 - €110,000", "₹2,500,000 - ₹3,500,000", "$160,000+",
    "$140,000", "Competitive", None
]

DATES = [
    "2026-10-15", "2026-10-18", "19/10/2026", "10-20-2026",
    "3 days ago", "1 day ago", "Just posted", "2026-10-21"
]


def generate_html_fixtures(output_dir: str = "data/fixtures/html") -> None:
    os.makedirs(output_dir, exist_ok=True)
    record_id = 1

    for page in range(1, 6):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TechCareers Portal - Page {page}</title>
</head>
<body>
    <header>
        <h1>TechCareers Engineering Portal</h1>
        <p>Active Job Listings - Page {page} of 5</p>
    </header>
    <main class="job-listings">
"""
        for i in range(25):
            t = TITLES[(i + (page - 1) * 5) % len(TITLES)]
            c = COMPANIES[(i * 3 + page) % len(COMPANIES)]
            l = LOCATIONS[(i * 2 + page) % len(LOCATIONS)]
            cat = CATEGORIES[(i + page) % len(CATEGORIES)]
            sal = SALARIES[(i * 7 + page) % len(SALARIES)]
            dt = DATES[(i + page) % len(DATES)]
            uid = f"job-{record_id:04d}"

            sal_html = f'        <span class="job-salary">{sal}</span>' if sal else '        <span class="job-salary empty"></span>'

            html += f"""        <div class="job-card" id="{uid}">
            <h2 class="job-title"><a class="job-link" href="https://example.com/jobs/{uid}">{t}</a></h2>
            <div class="company-name">{c}</div>
            <div class="job-location">{l}</div>
            <div class="job-category">{cat}</div>
    {sal_html}
            <div class="posted-date">{dt}</div>
        </div>
"""
            record_id += 1

        prev_link = f'<a class="prev-page" href="jobs_page_{page-1}.html">Previous</a>' if page > 1 else ''
        next_link = f'<a class="next-page" href="jobs_page_{page+1}.html">Next</a>' if page < 5 else ''

        html += f"""    </main>
    <footer class="pagination">
        {prev_link}
        <span class="current-page">Page {page} of 5</span>
        {next_link}
    </footer>
</body>
</html>"""
        with open(os.path.join(output_dir, f"jobs_page_{page}.html"), "w", encoding="utf-8") as f:
            f.write(html)

    print(f"Generated 5 HTML fixture pages with {record_id - 1} records in {output_dir}")


def generate_dirty_csv(output_path: str = "data/fixtures/dirty_jobs.csv") -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = ["Job Title", "Company Name", "Job Location", "Salary Range", "Category", "Posted Date", "URL"]
    
    rows = [
        # Normal record
        {"Job Title": "  Senior Data Engineer ", "Company Name": "Datheon Systems", "Job Location": "Remote", "Salary Range": "$140,000 - $160,000", "Category": "Data Engineering", "Posted Date": "2026-10-15", "URL": "https://example.com/jobs/101"},
        # Duplicate record (exact duplicate)
        {"Job Title": "  Senior Data Engineer ", "Company Name": "Datheon Systems", "Job Location": "Remote", "Salary Range": "$140,000 - $160,000", "Category": "Data Engineering", "Posted Date": "2026-10-15", "URL": "https://example.com/jobs/101"},
        # Messy whitespace & case
        {"Job Title": "etl PIPELINE SPECIALIST", "Company Name": " apex data labs ", "Job Location": "new york, ny", "Salary Range": "USD 125,000 - 150,000", "Category": "data engineering", "Posted Date": "19/10/2026", "URL": "https://example.com/jobs/102"},
        # Mixed currency GBP
        {"Job Title": "Cloud Infrastructure Engineer", "Company Name": "CloudScale Technologies", "Job Location": "London, UK", "Salary Range": "£85,000 - £100,000", "Category": "Cloud & DevOps", "Posted Date": "10-18-2026", "URL": "https://example.com/jobs/103"},
        # Missing salary & relative date
        {"Job Title": "Lead Python Developer", "Company Name": "Nexus Analytics", "Job Location": "Austin, TX", "Salary Range": "", "Category": "Backend Engineering", "Posted Date": "3 days ago", "URL": "https://example.com/jobs/104"},
        # INR currency with lakh separators
        {"Job Title": "Big Data Developer", "Company Name": "Synthetix AI", "Job Location": "Bangalore, India", "Salary Range": "₹2,500,000 - ₹3,500,000", "Category": "Data Engineering", "Posted Date": "2026-10-20", "URL": "https://example.com/jobs/105"},
        # Single number salary
        {"Job Title": "Machine Learning Engineer", "Company Name": "Hyperion Dynamics", "Job Location": "San Francisco, CA", "Salary Range": "$175,000", "Category": "Data Science & AI", "Posted Date": "1 day ago", "URL": "https://example.com/jobs/106"},
        # Non-numeric salary string
        {"Job Title": "Site Reliability Engineer", "Company Name": "Velocity Cloud", "Job Location": "Seattle, WA", "Salary Range": "Competitive salary + equity", "Category": "Cloud & DevOps", "Posted Date": "2026-10-17", "URL": "https://example.com/jobs/107"},
        # Missing location (null default to Remote)
        {"Job Title": "Analytics Engineer", "Company Name": "Acuity Logic", "Job Location": "   ", "Salary Range": "$110,000 - $130,000", "Category": "Data Engineering", "Posted Date": "2026-10-14", "URL": "https://example.com/jobs/108"},
        # Schema violation: missing required title
        {"Job Title": "", "Company Name": "Anonymous Corp", "Job Location": "Remote", "Salary Range": "$100,000", "Category": "Engineering", "Posted Date": "2026-10-12", "URL": "https://example.com/jobs/109"},
    ]

    # Add 20 more diverse rows
    for i in range(110, 130):
        rows.append({
            "Job Title": f"Data Engineer Level {i % 4 + 1}",
            "Company Name": f"TechCorp {i % 6 + 1}",
            "Job Location": "Remote" if i % 2 == 0 else "New York, NY",
            "Salary Range": f"${90 + (i % 10)*10},000 - ${110 + (i % 10)*10},000",
            "Category": "Data Engineering",
            "Posted Date": f"2026-10-{(i % 20) + 1:02d}",
            "URL": f"https://example.com/jobs/{i}"
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated dirty CSV dataset with {len(rows)} records at {output_path}")


if __name__ == "__main__":
    generate_html_fixtures()
    generate_dirty_csv()
