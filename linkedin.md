# 🚀 DataFlow Engineering Studio — LinkedIn Post Announcement

> **Attachment**: Attach [`image.png`](file:///d:/intership/Datheon_Python_for_Data_Engineering_&_Automation_Internship/rw/image.png) or [`assets/linkedin_post.svg`](file:///d:/intership/Datheon_Python_for_Data_Engineering_&_Automation_Internship/rw/assets/linkedin_post.svg) with this post.

---

### 📝 Ready-to-Publish Post Text (Copy & Paste below)

Excited to share my latest capstone project: **DataFlow Engineering Studio** — an autonomous, production-ready data engineering and ETL automation system built with Python! ⚡📊

As part of my Data Engineering & Automation Internship with Datheon, I engineered a modular suite of **four decoupled Python applications** that solve the entire data lifecycle: from resilient web scraping to clean schema transformation, idempotent relational database ingestion, and scheduled orchestration with rotating logs and alerting.

Everything is unified through a modern local dashboard built with **Streamlit**! 🖥️✨

---

### 🛠️ What I Built:

1️⃣ **Project 1: Autonomous Web Scraper & Extractor**
- Built with `Requests` and `BeautifulSoup4`.
- Features polite crawling etiquette: configurable User-Agent, request timeouts, 3x exponential backoff retries, rate-limiting delays, and `robots.txt` compliance.
- Implemented canonical SHA-256 natural key fingerprinting to prevent duplicate record acquisition.
- Extracts 125+ structured records with offline HTML fixtures for repeatable, zero-network evaluation.

2️⃣ **Project 2: Automated Data Cleaning & Schema Transformation**
- Built with `Pandas`.
- Normalizes headers to standard `snake_case`, collapses irregular whitespace, and handles pseudo-null values (`"N/A"`, `"none"`, `"competitive"`).
- Normalizes currencies into numeric ranges while strictly preserving ISO currency codes (`USD`, `EUR`, `GBP`, `INR`) without speculative FX conversion.
- Normalizes diverse date formats (US, EU, ISO, and relative dates like *"3 days ago"*) into standard `YYYY-MM-DD`.
- Enforces strict column typing, boundaries, and non-null constraints against `config/schema.json` with a detailed Data Quality Audit Report.

3️⃣ **Project 3: Relational Ingestion & Upsert Engine**
- Built with `SQLAlchemy 2.0` (SQLite default, PostgreSQL optional).
- Guarantees **idempotent upserts**: re-running the exact same dataset 100 times results in **0 duplicate rows**, updating changed attributes in-place.
- Implemented atomic batch transactions with rollback isolation (tested and proven to prevent orphan rows on exceptions).
- Includes built-in analytical query verifications for salary aggregations, duplicate audits, and role filtering.

4️⃣ **Project 4: Scheduled End-to-End ETL Pipeline with Alerting**
- Orchestrates an 8-stage pipeline:
  `Extract ──► Validate In ──► Transform ──► Validate Out ──► Load/Upsert ──► Verify ──► Report ──► Notify`
- Features a mutual exclusion file lock (`.pipeline.lock`) to prevent accidental duplicate concurrent runs.
- Rotating log files (`logs/pipeline.log`) with log level controls.
- Safe multi-channel notifications (Console fallback, Webhooks, SMTP).
- Includes dry-run simulation mode (`--dry-run`) and periodic execution via Python `schedule`, Linux cron, and Windows Task Scheduler.

5️⃣ **Central Streamlit Dashboard (`app.py`)**
- A responsive, modern studio linking all 4 projects: interactive scraper parameters, before-and-after data comparisons, database explorer, rollback tests, and real-time scheduler controls.

---

### 📈 Verified Engineering Metrics:
- 🧪 **25 / 25 Pytest Tests Passing** (100% green across unit, integration, and E2E suites)
- 📦 **125+ Verified Extracted Records**
- 🛡️ **0 Duplicate Rows** (Rigorous business key idempotency)
- 🔄 **30 Atomic Conventional Git Commits**
- 🌐 **100% Offline-Runnable & Verifiable** (Zero external paid APIs, Docker, or DB server requirements)

---

🔗 **GitHub Repository**: https://github.com/rajeshwari229080/Datheon_Python_for_Data_Engineering_-_Automation_Internship

A big thank you to my mentors at Datheon for the guidance and practical problem statements! Looking forward to hearing your thoughts and feedback from the data engineering community. 💬👇

#DataEngineering #Python #ETL #WebScraping #SQLAlchemy #Pandas #Streamlit #DataAutomation #SoftwareEngineering #DatabaseDesign #PostgreSQL #SQLite #CleanCode #InternshipProject
