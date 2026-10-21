"""Unit and integration tests for Project 3: Relational Database Auto-Ingestion & Upsert Engine."""
import os
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, JobPosting
from src.database.engine import DatabaseEngineFactory
from src.database.upsert import DatabaseUpsertEngine
from src.database.verifier import DatabaseQueryVerifier
from projects.project_3_database_ingestion.run import run_database_ingestion


@pytest.fixture
def test_db_session(tmp_path):
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"
    factory = DatabaseEngineFactory(db_url)
    factory.create_tables()
    session = factory.get_session()
    yield session, db_url
    session.close()


def test_table_creation(test_db_session):
    session, db_url = test_db_session
    engine = session.get_bind()
    table_names = Base.metadata.tables.keys()
    assert "job_postings" in table_names
    assert "etl_run_history" in table_names


def test_insert_and_idempotent_upsert(test_db_session):
    session, _ = test_db_session
    upsert = DatabaseUpsertEngine(session, batch_size=10)

    records = [
        {
            "record_hash": "hash_101",
            "title": "Data Engineer",
            "organization": "Datheon",
            "location": "Remote",
            "salary_min": 120000.0,
            "salary_max": 140000.0,
            "currency": "USD",
            "category": "Data Engineering",
            "posted_date": "2026-10-18",
            "source_url": "https://example.com/101",
            "extracted_at": "2026-10-21 12:00:00"
        },
        {
            "record_hash": "hash_102",
            "title": "Cloud Architect",
            "organization": "Apex Labs",
            "location": "New York, NY",
            "salary_min": 150000.0,
            "salary_max": 180000.0,
            "currency": "USD",
            "category": "Cloud",
            "posted_date": "2026-10-19",
            "source_url": "https://example.com/102",
            "extracted_at": "2026-10-21 12:00:00"
        }
    ]

    # Pass 1: Initial Ingestion
    m1 = upsert.upsert_records(records)
    assert m1.inserted == 2
    assert m1.updated == 0
    assert m1.unchanged == 0

    # Pass 2: Re-ingest exact same records (Idempotency assertion)
    m2 = upsert.upsert_records(records)
    assert m2.inserted == 0
    assert m2.updated == 0
    assert m2.unchanged == 2

    # Pass 3: Modify non-key field (salary_max) and reload
    modified_records = [dict(records[0])]
    modified_records[0]["salary_max"] = 165000.0
    m3 = upsert.upsert_records(modified_records)
    assert m3.updated == 1
    assert m3.inserted == 0

    # Verify updated value in database
    job = session.query(JobPosting).filter_by(record_hash="hash_101").first()
    assert job.salary_max == 165000.0


def test_transaction_rollback(test_db_session):
    session, _ = test_db_session
    verifier = DatabaseQueryVerifier(session)
    assert verifier.verify_transaction_rollback() is True


def test_analytical_queries(test_db_session):
    session, _ = test_db_session
    upsert = DatabaseUpsertEngine(session, batch_size=10)
    records = [
        {
            "record_hash": f"hash_{i}",
            "title": f"Engineer {i}",
            "organization": "Datheon Systems" if i % 2 == 0 else "Apex Labs",
            "location": "Remote" if i % 2 == 0 else "Austin, TX",
            "category": "Engineering" if i < 3 else "Analytics",
            "salary_min": 100000.0 + i * 5000,
            "salary_max": 120000.0 + i * 5000,
            "currency": "USD",
            "source_url": f"https://example.com/{i}",
            "extracted_at": "2026-10-21 12:00:00"
        }
        for i in range(5)
    ]
    upsert.upsert_records(records)

    verifier = DatabaseQueryVerifier(session)
    total, dups = verifier.check_duplicates()
    assert total == 5
    assert dups == 0

    cats = verifier.get_category_aggregations()
    assert len(cats) == 2

    orgs = verifier.get_top_organizations(5)
    assert len(orgs) == 2

    stats = verifier.get_salary_statistics()
    assert stats["min_salary"] == 100000.0
    assert stats["max_salary"] == 140000.0


def test_dry_run_does_not_modify_db(test_db_session):
    session, _ = test_db_session
    upsert = DatabaseUpsertEngine(session, batch_size=10)
    records = [{
        "record_hash": "hash_dry_run",
        "title": "Dry Run Job",
        "organization": "Ghost Org",
        "location": "Remote",
        "source_url": "https://example.com/dry",
        "extracted_at": "2026-10-21 12:00:00"
    }]
    metrics = upsert.upsert_records(records, dry_run=True)
    assert metrics.inserted == 1

    # Assert row was NOT written to database
    job = session.query(JobPosting).filter_by(record_hash="hash_dry_run").first()
    assert job is None
