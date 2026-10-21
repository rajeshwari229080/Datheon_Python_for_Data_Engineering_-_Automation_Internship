"""DataFlow Engineering Studio — Central Unified Dashboard
A professional, interactive local dashboard linking all four independent projects:
- Project 1: Autonomous Web Scraper & Data Extractor
- Project 2: Automated Data Cleaning & Schema Transformation
- Project 3: Relational Database Auto-Ingestion & Upsert Engine
- Project 4: Scheduled End-to-End ETL Pipeline with Alerting
"""
import io
import json
import logging
import os
import sys
import time
import pandas as pd
import streamlit as st

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.scraper.client import PoliteHttpClient
from src.scraper.extractor import HtmlExtractor
from src.scraper.dedup import RecordDeduplicator
from src.scraper.reporter import ScrapingReporter
from projects.project_1_scraper.run import run_scraper
from projects.project_2_data_cleaning.run import clean_dataset
from projects.project_3_database_ingestion.run import run_database_ingestion
from src.database.engine import DatabaseEngineFactory
from src.database.verifier import DatabaseQueryVerifier
from src.pipeline.orchestrator import EtlOrchestrator
from src.pipeline.scheduler import EtlScheduler

# Set Page Config
st.set_page_config(
    page_title="DataFlow Engineering Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(226, 232, 240, 0.2);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .badge-success {
        background-color: #dcfce7;
        color: #15803d;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-info {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Top Bar
st.markdown('<div class="main-title">DataFlow Engineering Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Autonomous Web Scraping, Data Cleaning, Relational Ingestion & Scheduled ETL Automation</div>', unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Studio Navigation")
nav_selection = st.sidebar.radio(
    "Go to View:",
    [
        "🏛️ Studio Overview",
        "🕷️ Project 1: Web Scraper",
        "🧹 Project 2: Data Cleaning",
        "🗄️ Project 3: Database Engine",
        "⏱️ Project 4: Scheduled ETL Pipeline",
        "📊 Execution Telemetry & Logs"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### System Environment")
db_url_env = os.getenv("DATABASE_URL", "sqlite:///database/dataflow.db")
db_masked = db_url_env if "@" not in db_url_env else f"{db_url_env.split('://')[0]}://***@{db_url_env.split('@')[1]}"
st.sidebar.code(f"DB: {db_masked}\nPython: {sys.version.split()[0]}\nStatus: Healthy", language="text")

# ==============================================================================
# VIEW 1: STUDIO OVERVIEW
# ==============================================================================
if nav_selection == "🏛️ Studio Overview":
    st.subheader("System Architecture & Project Suite")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Project 1</h4>
            <p><strong>Web Scraper</strong></p>
            <p class="badge-info">Requests + BS4</p>
            <p style="font-size:0.85rem; color:#64748b; margin-top:8px;">Extracts 125+ records with polite backoff & robots parsing</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Project 2</h4>
            <p><strong>Data Cleaning</strong></p>
            <p class="badge-info">Pandas + Schema</p>
            <p style="font-size:0.85rem; color:#64748b; margin-top:8px;">Snake_case, null sanitization, currency & ISO dates</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Project 3</h4>
            <p><strong>Database Engine</strong></p>
            <p class="badge-info">SQLAlchemy 2.0</p>
            <p style="font-size:0.85rem; color:#64748b; margin-top:8px;">Idempotent upsert, transaction rollback & analytics</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>Project 4</h4>
            <p><strong>Scheduled ETL</strong></p>
            <p class="badge-info">Schedule + Alerting</p>
            <p style="font-size:0.85rem; color:#64748b; margin-top:8px;">8-Stage orchestration, locks, run IDs & rotating logs</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### End-to-End ETL Flow Diagram")
    st.code("""
[1. Extract]         Requests & BeautifulSoup4 multi-page extraction with SHA-256 fingerprinting
       │
[2. Validate Input]  Verify record presence and raw payload integrity
       │
[3. Transform]       Pandas cleaning: snake_case, null sanitization, currency & date parsing
       │
[4. Validate Output] Enforce strict schema constraints against config/schema.json
       │
[5. Load / Upsert]   SQLAlchemy dual-dialect batch upserts (SQLite / PostgreSQL)
       │
[6. Verify]          Analytical queries, business key duplicate audit & rollback test
       │
[7. Report]          Audit logs & metrics to reports/pipeline_summary.json & SQLite history table
       │
[8. Notify]          Multi-channel alert dispatch (Console fallback / Webhook / SMTP)
    """, language="text")

    st.markdown("### Quick System Status")
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        st.markdown("**Dataset Artifacts Status:**")
        raw_exists = os.path.exists("data/raw/scraped_jobs.csv")
        proc_exists = os.path.exists("data/processed/cleaned_jobs.csv")
        db_exists = os.path.exists("database/dataflow.db")
        st.write(f"- Raw Extracted CSV: `{'✅ Available' if raw_exists else '❌ Not Generated Yet'}`")
        st.write(f"- Cleaned Processed CSV: `{'✅ Available' if proc_exists else '❌ Not Generated Yet'}`")
        st.write(f"- Relational Database: `{'✅ Available' if db_exists else '❌ Not Initialized'}`")
    with q_col2:
        st.markdown("**Quick Trigger Actions:**")
        if st.button("🚀 Run Complete Pipeline (Manual Trigger)", type="primary"):
            with st.spinner("Executing end-to-end pipeline stages..."):
                orchestrator = EtlOrchestrator()
                state = orchestrator.run_pipeline(dry_run=False)
                if state.status == "SUCCESS":
                    st.success(f"Pipeline finished successfully! Run ID: {state.run_id} ({state.duration_seconds}s)")
                else:
                    st.error(f"Pipeline failed: {state.error_message}")


# ==============================================================================
# VIEW 2: PROJECT 1 - WEB SCRAPER
# ==============================================================================
elif nav_selection == "🕷️ Project 1: Web Scraper":
    st.subheader("Project 1: Autonomous Web Scraper & Data Extractor")
    st.markdown("Extract structured records from paginated web portals or realistic multi-page HTML test fixtures.")

    p1_col1, p1_col2 = st.columns([1, 2])
    with p1_col1:
        st.markdown("#### Scraper Configuration")
        mode = st.radio("Extraction Source:", ["Offline Multi-Page HTML Fixtures (125 Records)", "Live Web Scraping"])
        max_pages = st.slider("Max Pages to Scrape:", min_value=1, max_value=5, value=5)
        max_records = st.number_input("Max Records Limit:", min_value=10, max_value=200, value=150)

        run_p1_btn = st.button("▶️ Execute Scraper", type="primary")

    with p1_col2:
        st.markdown("#### Execution Output")
        if run_p1_btn:
            with st.spinner("Extracting web records..."):
                is_live = (mode == "Live Web Scraping")
                summary = run_scraper(
                    config_path="config/scraper_config.json",
                    force_live=is_live,
                    override_max_pages=max_pages,
                    override_max_records=max_records
                )
                st.success(f"Extraction complete in {summary.get('duration_seconds')}s! Extracted: {summary.get('records_extracted')}, Unique: {summary.get('records_extracted') - summary.get('duplicates_removed')}")

    # Display Extracted Data
    raw_csv = "data/raw/scraped_jobs.csv"
    if os.path.exists(raw_csv):
        st.markdown("#### Extracted Records Preview")
        df_raw = pd.read_csv(raw_csv)
        st.dataframe(df_raw, use_container_width=True)

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                "📥 Download Raw CSV",
                df_raw.to_csv(index=False),
                file_name="scraped_jobs.csv",
                mime="text/csv"
            )
        with d_col2:
            raw_json_path = "data/raw/scraped_jobs.json"
            if os.path.exists(raw_json_path):
                with open(raw_json_path, "r", encoding="utf-8") as f:
                    json_str = f.read()
                st.download_button(
                    "📥 Download Raw JSON",
                    json_str,
                    file_name="scraped_jobs.json",
                    mime="application/json"
                )


# ==============================================================================
# VIEW 3: PROJECT 2 - DATA CLEANING
# ==============================================================================
elif nav_selection == "🧹 Project 2: Data Cleaning":
    st.subheader("Project 2: Automated Data Cleaning & Schema Transformation")
    st.markdown("Sanitizes messy datasets: normalizes headers to snake_case, cleans nulls, parses currencies and dates, and validates schema constraints.")

    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        st.markdown("#### Input Dataset Selection")
        source_opt = st.selectbox(
            "Select Input Source:",
            ["Scraped Raw Dataset (data/raw/scraped_jobs.csv)", "Sample Dirty Dataset (data/fixtures/dirty_jobs.csv)", "Upload Custom CSV"]
        )

        uploaded_file = None
        custom_input_path = None
        if source_opt == "Upload Custom CSV":
            uploaded_file = st.file_uploader("Upload CSV File:", type=["csv"])
            if uploaded_file:
                custom_input_path = "data/raw/uploaded_raw.csv"
                with open(custom_input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
        elif source_opt == "Sample Dirty Dataset (data/fixtures/dirty_jobs.csv)":
            custom_input_path = "data/fixtures/dirty_jobs.csv"
        else:
            custom_input_path = "data/raw/scraped_jobs.csv"

        run_cleaner_btn = st.button("▶️ Clean & Validate Dataset", type="primary")

    with c_col2:
        st.markdown("#### Data Quality Metrics")
        if run_cleaner_btn:
            with st.spinner("Transforming and validating schema..."):
                res = clean_dataset(input_path=custom_input_path)
                st.success("Data cleaning & validation completed successfully!")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Input Rows", res.get("input_records"))
                m2.metric("Output Rows", res.get("output_records"))
                m3.metric("Duplicates Removed", res.get("duplicates_removed"))
                m4.metric("Rejected Rows", res.get("rejected_records"))

    # Display Cleaned Dataset
    clean_csv = "data/processed/cleaned_jobs.csv"
    if os.path.exists(clean_csv):
        st.markdown("#### Cleaned & Validated Records")
        df_clean = pd.read_csv(clean_csv)
        st.dataframe(df_clean, use_container_width=True)

        st.download_button(
            "📥 Download Cleaned CSV",
            df_clean.to_csv(index=False),
            file_name="cleaned_jobs.csv",
            mime="text/csv"
        )


# ==============================================================================
# VIEW 4: PROJECT 3 - DATABASE ENGINE
# ==============================================================================
elif nav_selection == "🗄️ Project 3: Database Engine":
    st.subheader("Project 3: Relational Database Auto-Ingestion & Upsert Engine")
    st.markdown("Idempotent batch loading into SQLite / PostgreSQL with transaction rollback guarantees and query verification.")

    db_factory = DatabaseEngineFactory()
    db_factory.create_tables()
    session = db_factory.get_session()
    verifier = DatabaseQueryVerifier(session)

    total_rows, dup_count = verifier.check_duplicates()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Table Rows", total_rows)
    m2.metric("Duplicate Business Keys", dup_count)
    m3.metric("Database Health", "Connected (100%)" if db_factory.ping() else "Disconnected")
    m4.metric("Dialect", "SQLite 3" if "sqlite" in db_factory.database_url else "PostgreSQL")

    tab1, tab2, tab3 = st.tabs(["🚀 Ingestion Controls", "🔍 Analytical Explorer", "🛡️ Rollback & Integrity Test"])

    with tab1:
        st.markdown("#### Run Batch Upsert Ingestion")
        dry_run_opt = st.checkbox("Dry-Run Mode (Simulate without committing writes)", value=False)
        batch_size_opt = st.number_input("Batch Size:", min_value=10, max_value=200, value=50)

        if st.button("▶️ Execute Ingestion", type="primary"):
            with st.spinner("Ingesting records into database..."):
                res = run_database_ingestion(
                    input_file="data/processed/cleaned_jobs.csv",
                    batch_size=batch_size_opt,
                    dry_run=dry_run_opt
                )
                m = res["ingestion_metrics"]
                st.success(f"Ingestion finished! Inserted: {m['inserted']}, Updated: {m['updated']}, Unchanged: {m['unchanged']} in {m['duration_seconds']}s")

    with tab2:
        st.markdown("#### Analytical Search & Aggregations")
        search_kw = st.text_input("Filter by Job Title or Organization:", "")
        min_sal = st.number_input("Minimum Salary Filter (USD):", min_value=0, max_value=300000, value=0)

        filtered_records = verifier.filter_and_sort_jobs(
            min_salary=min_sal if min_sal > 0 else None,
            search_keyword=search_kw if search_kw else None
        )
        if filtered_records:
            st.dataframe(pd.DataFrame(filtered_records), use_container_width=True)
        else:
            st.info("No matching records found for given filters.")

        st.markdown("#### Category Breakdown")
        cats = verifier.get_category_aggregations()
        if cats:
            st.dataframe(pd.DataFrame(cats), use_container_width=True)

    with tab3:
        st.markdown("#### Transaction Rollback Safety Verification")
        st.markdown("This test deliberately attempts to insert an invalid record and forces an exception during transaction execution to confirm that zero orphaned rows are committed.")
        if st.button("🛡️ Execute Rollback Safety Audit"):
            passed = verifier.verify_transaction_rollback()
            if passed:
                st.success("✅ Rollback audit PASSED! Atomic rollback preserved database integrity.")
            else:
                st.error("❌ Rollback test failed!")

    session.close()


# ==============================================================================
# VIEW 5: PROJECT 4 - SCHEDULED ETL PIPELINE
# ==============================================================================
elif nav_selection == "⏱️ Project 4: Scheduled ETL Pipeline":
    st.subheader("Project 4: Scheduled End-to-End ETL Pipeline with Alerting")
    st.markdown("Orchestrates all stages with mutual exclusion locks, telemetry, rotating logging, and background scheduling.")

    # Initialize session state for scheduler
    if "scheduler_running" not in st.session_state:
        st.session_state.scheduler_running = False
    if "scheduler_instance" not in st.session_state:
        st.session_state.scheduler_instance = None

    p4_col1, p4_col2 = st.columns([1, 1])

    with p4_col1:
        st.markdown("#### Pipeline Manual Trigger")
        dry_run_mode = st.checkbox("Dry Run (Validate without modifying database)", value=False)
        live_mode = st.checkbox("Force Live Scraping (Default: local fixtures)", value=False)

        if st.button("🚀 Trigger Immediate Pipeline Run", type="primary"):
            with st.spinner("Executing pipeline through all 8 stages..."):
                orch = EtlOrchestrator()
                state = orch.run_pipeline(dry_run=dry_run_mode, force_live_scrape=live_mode)
                if state.status in ("SUCCESS", "DRY_RUN"):
                    st.success(f"Pipeline completed: {state.status}! Run ID: {state.run_id} ({state.duration_seconds}s)")
                else:
                    st.error(f"Pipeline failed: {state.error_message}")

    with p4_col2:
        st.markdown("#### Background Scheduler Controller")
        interval_min = st.number_input("Execution Interval (Minutes):", min_value=1, max_value=1440, value=60)
        
        status_txt = "🟢 Running in Background" if st.session_state.scheduler_running else "⚪ Idle / Stopped"
        st.markdown(f"**Scheduler Status:** `{status_txt}`")

        s_btn_col1, s_btn_col2 = st.columns(2)
        with s_btn_col1:
            if st.button("▶️ Start Scheduler"):
                if not st.session_state.scheduler_running:
                    sched = EtlScheduler(interval_minutes=interval_min)
                    sched.start_in_background()
                    st.session_state.scheduler_instance = sched
                    st.session_state.scheduler_running = True
                    st.rerun()
        with s_btn_col2:
            if st.button("⏹️ Stop Scheduler"):
                if st.session_state.scheduler_running and st.session_state.scheduler_instance:
                    st.session_state.scheduler_instance.stop()
                    st.session_state.scheduler_running = False
                    st.session_state.scheduler_instance = None
                    st.rerun()

    st.markdown("---")
    st.markdown("#### Recent Run History")
    history_file = "reports/run_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            runs = json.load(f)
        if runs:
            summary_table = []
            for r in runs[:10]:
                summary_table.append({
                    "Run ID": r.get("run_id"),
                    "Status": r.get("status"),
                    "Extracted": r.get("records_extracted"),
                    "Cleaned": r.get("records_cleaned"),
                    "Inserted": r.get("records_inserted"),
                    "Updated": r.get("records_updated"),
                    "Unchanged": r.get("records_unchanged"),
                    "Duration (s)": r.get("duration_seconds"),
                    "Ended At": r.get("ended_at")
                })
            st.dataframe(pd.DataFrame(summary_table), use_container_width=True)


# ==============================================================================
# VIEW 6: EXECUTION TELEMETRY & LOGS
# ==============================================================================
elif nav_selection == "📊 Execution Telemetry & Logs":
    st.subheader("System Telemetry, Quality Audits & Rotating Logs")

    log_tab, quality_tab = st.tabs(["📜 Pipeline Rotating Logs", "📋 Data Quality Audit Report"])

    with log_tab:
        log_file = "logs/pipeline.log"
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            log_content = "".join(lines[-150:])  # Last 150 lines
            st.code(log_content or "Log file is currently empty.", language="text")
        else:
            st.info("Log file 'logs/pipeline.log' has not been created yet.")

    with quality_tab:
        qual_file = "reports/data_quality_report.json"
        if os.path.exists(qual_file):
            with open(qual_file, "r", encoding="utf-8") as f:
                report_dict = json.load(f)
            st.json(report_dict)
        else:
            st.info("Quality report has not been generated yet.")
