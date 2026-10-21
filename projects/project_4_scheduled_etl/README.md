# Project 4: Scheduled End-to-End ETL Pipeline with Alerting

Part of the **DataFlow Engineering Studio** internship project suite.

## Overview
Project 4 unifies extraction, validation, cleaning, database ingestion, reporting, and alerting into a robust, repeatable pipeline. It follows the required stage architecture:
`Extract -> Validate Input -> Transform -> Validate Output -> Load/Upsert -> Verify -> Report -> Notify`

## Key Features
- **Deterministic Stage Progression**: Strict sequential validation with failure stops.
- **Mutual Exclusion File Lock**: Guarantees no concurrent colliding executions (`.pipeline.lock`).
- **Telemetry & Rotating Logs**: Captures per-stage duration, records in/out, rotating log files (`logs/pipeline.log`).
- **Safe Multi-Channel Alerting**: Console, Webhook, and SMTP alerts with automatic fallback when credentials are absent.
- **Dry-Run Mode**: Validates transformations and simulates upserts without committing database writes.
- **Run-History Auditing**: Saves execution status into `reports/run_history.json` and the relational table `etl_run_history`.

## Quick Start

### 1. Run Complete Pipeline (Manual Single Run)
```bash
python projects/project_4_scheduled_etl/run.py
```

### 2. Run in Dry-Run Mode
```bash
python projects/project_4_scheduled_etl/run.py --dry-run
```

### 3. Run in Lightweight Scheduled Mode (Every 30 Minutes)
```bash
python projects/project_4_scheduled_etl/run.py --schedule --interval 30
```

---

## Operating System Scheduling Alternatives

### A. Linux / macOS Crontab
To run every hour using system cron:
```bash
crontab -e
# Add the following entry:
0 * * * * cd /path/to/DataFlow_Engineering_Studio && /usr/bin/python3 projects/project_4_scheduled_etl/run.py >> logs/cron.log 2>&1
```

### B. Windows Task Scheduler
To schedule on Windows via PowerShell:
```powershell
$Action = New-ScheduledTaskAction -Execute "python.exe" -Argument "projects/project_4_scheduled_etl/run.py" -WorkingDirectory "D:\intership\Datheon_Python_for_Data_Engineering_&_Automation_Internship\rw"
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
Register-ScheduledTask -TaskName "DataFlow_Hourly_ETL" -Action $Action -Trigger $Trigger -Description "Automated DataFlow Studio ETL Pipeline"
```
