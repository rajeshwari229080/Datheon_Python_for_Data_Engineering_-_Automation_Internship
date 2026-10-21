"""Logging configuration and consolidated report generator.
Sets up rotating file handlers and generates consolidated HTML/Markdown run summaries.
"""
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Any, Dict, Optional


def configure_pipeline_logger(
    log_file_path: str = "logs/pipeline.log",
    log_level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3
) -> logging.Logger:
    """Configure root and pipeline rotating file and console logger."""
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    logger = logging.getLogger("dataflow")
    logger.setLevel(log_level)

    # Avoid duplicate handlers on re-initialization
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Rotating file handler
        rf_handler = RotatingFileHandler(
            log_file_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        rf_handler.setFormatter(formatter)
        rf_handler.setLevel(log_level)
        logger.addHandler(rf_handler)

        # Console handler
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(formatter)
        c_handler.setLevel(log_level)
        logger.addHandler(c_handler)

    return logger


class ConsolidatedReportGenerator:
    """Generates human-readable Markdown and HTML summaries combining all 4 projects."""

    @staticmethod
    def generate_html_summary(run_data: Dict[str, Any]) -> str:
        """Create clean HTML report summarizing pipeline run state."""
        stages_html = "".join(
            f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>{name.upper()}</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd; color: {'#28a745' if s.get('status')=='COMPLETED' else '#dc3545'};"><strong>{s.get('status')}</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{s.get('duration_seconds')}s</td>
                <td style="padding: 8px; border: 1px solid #ddd;">In: {s.get('records_in')}, Out: {s.get('records_out')}</td>
            </tr>
            """
            for name, s in run_data.get("stages", {}).items()
        )

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ETL Execution Report - {run_data.get('run_id')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #333; }}
        .card {{ background: #fdfdfd; border: 1px solid #e0e0e0; border-radius: 8px; padding: 24px; max-width: 900px; margin: auto; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        h1 {{ color: #1a202c; font-size: 24px; border-bottom: 2px solid #edf2f7; padding-bottom: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #f7fafc; padding: 10px; border: 1px solid #ddd; text-align: left; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 14px; background: {'#d4edda' if run_data.get('status')=='SUCCESS' else '#f8d7da'}; color: {'#155724' if run_data.get('status')=='SUCCESS' else '#721c24'}; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>DataFlow Engineering Studio — ETL Execution Report</h1>
        <p><strong>Run ID:</strong> {run_data.get('run_id')} &nbsp;|&nbsp; <span class="badge">{run_data.get('status')}</span></p>
        <p><strong>Execution Window:</strong> {run_data.get('started_at')} to {run_data.get('ended_at')} ({run_data.get('duration_seconds')}s)</p>
        <p><strong>Records:</strong> Extracted {run_data.get('records_extracted')}, Cleaned {run_data.get('records_cleaned')}, Inserted {run_data.get('records_inserted')}, Updated {run_data.get('records_updated')}, Unchanged {run_data.get('records_unchanged')}</p>
        
        <h2>Stage Execution Telemetry</h2>
        <table>
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Records Flow</th>
                </tr>
            </thead>
            <tbody>
                {stages_html}
            </tbody>
        </table>
    </div>
</body>
</html>"""
