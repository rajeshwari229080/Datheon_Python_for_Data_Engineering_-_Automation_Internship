-- =============================================================================
-- DataFlow Engineering Studio - Relational Query Verification Scripts
-- Table: job_postings
-- Dialect: SQLite 3 / ANSI SQL Compatible
-- =============================================================================

-- 1. Total Record Count Audit
SELECT COUNT(*) AS total_records FROM job_postings;

-- 2. Business Key Duplicate Check (Should ALWAYS return 0 duplicates)
SELECT 
    record_hash, 
    COUNT(*) AS occurrences
FROM job_postings
GROUP BY record_hash
HAVING COUNT(*) > 1;

-- 3. Category Breakdown with Average and Maximum Salary
SELECT 
    category,
    COUNT(id) AS total_jobs,
    ROUND(AVG(salary_min), 2) AS avg_min_salary,
    ROUND(AVG(salary_max), 2) AS avg_max_salary,
    MAX(salary_max) AS highest_salary
FROM job_postings
GROUP BY category
ORDER BY total_jobs DESC;

-- 4. Top Hiring Organizations
SELECT 
    organization,
    COUNT(id) AS active_postings,
    MIN(salary_min) AS min_offer,
    MAX(salary_max) AS max_offer
FROM job_postings
GROUP BY organization
ORDER BY active_postings DESC
LIMIT 10;

-- 5. High-Compensation Remote Engineering Jobs (Filtered & Sorted)
SELECT 
    title,
    organization,
    location,
    salary_min,
    salary_max,
    currency,
    posted_date
FROM job_postings
WHERE 
    salary_min >= 120000 
    AND (location LIKE '%Remote%' OR location IS NULL)
ORDER BY salary_min DESC
LIMIT 20;

-- 6. Audit Trail: Ingestion Window & Freshness
SELECT 
    MIN(created_at) AS first_record_ingested_at,
    MAX(created_at) AS latest_record_ingested_at,
    COUNT(CASE WHEN updated_at > created_at THEN 1 END) AS records_updated_in_place
FROM job_postings;
