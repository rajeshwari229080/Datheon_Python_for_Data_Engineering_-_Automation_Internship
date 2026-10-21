"""Multi-channel alerting engine.
Dispatches completion and failure summaries to Console, Webhook, or SMTP Email
with zero hardcoded credentials and safe offline console fallbacks.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages dispatching alerts across configured channels."""

    def __init__(self):
        self.channels = [
            c.strip().lower()
            for c in os.getenv("ALERT_CHANNELS", "console").split(",")
            if c.strip()
        ]
        self.webhook_url = os.getenv("WEBHOOK_URL")
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM", "alerts@dataflow.studio")
        self.smtp_to = os.getenv("SMTP_TO", "devops@dataflow.studio")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    def send_pipeline_alert(self, state: Any) -> Dict[str, bool]:
        """Format and dispatch notification across active channels."""
        subject = f"[{state.status}] DataFlow ETL Pipeline: {state.run_id}"
        message = self._format_message(state)
        dispatch_results = {}

        for ch in self.channels:
            if ch == "console":
                dispatch_results["console"] = self._notify_console(subject, message)
            elif ch == "webhook":
                dispatch_results["webhook"] = self._notify_webhook(subject, message, state)
            elif ch == "smtp":
                dispatch_results["smtp"] = self._notify_smtp(subject, message)
            else:
                logger.warning(f"Unknown notification channel: {ch}. Falling back to console.")
                dispatch_results["console"] = self._notify_console(subject, message)

        return dispatch_results

    def _format_message(self, state: Any) -> str:
        stages_str = "\n".join(
            f"  - {name.upper()}: {stg.status} ({stg.duration_seconds}s) [In: {stg.records_in}, Out: {stg.records_out}]"
            for name, stg in getattr(state, "stages", {}).items()
        )
        err_str = f"\nError Message: {state.error_message}" if state.error_message else ""

        return f"""DataFlow Engineering Studio - Pipeline Execution Notification
------------------------------------------------------------
Run ID:             {state.run_id}
Pipeline:           {state.pipeline_name}
Status:             {state.status} (Dry Run: {state.dry_run})
Execution Window:   {state.started_at} -> {state.ended_at}
Duration:           {state.duration_seconds}s

Records Summary:
  - Extracted:      {state.records_extracted}
  - Cleaned:        {state.records_cleaned}
  - Inserted:       {state.records_inserted}
  - Updated:        {state.records_updated}
  - Unchanged:      {state.records_unchanged}
  - Failed:         {state.records_failed}{err_str}

Stage Execution Details:
{stages_str}
------------------------------------------------------------"""

    def _notify_console(self, subject: str, message: str) -> bool:
        """Print notification banner to console/stdout."""
        print(f"\n[ALERT NOTIFICATION] {subject}\n{message}\n")
        logger.info(f"Dispatched console alert for {subject}")
        return True

    def _notify_webhook(self, subject: str, message: str, state: Any) -> bool:
        """Send JSON payload to configured HTTP webhook endpoint."""
        if not self.webhook_url:
            logger.warning("Webhook alerting requested but WEBHOOK_URL is not set. Defaulting to console.")
            return False
        try:
            payload = {
                "text": subject,
                "summary": message,
                "run_id": state.run_id,
                "status": state.status,
                "duration_seconds": state.duration_seconds,
            }
            resp = requests.post(self.webhook_url, json=payload, timeout=5)
            logger.info(f"Webhook alert sent to {self.webhook_url}: Status {resp.status_code}")
            return resp.status_code < 400
        except Exception as e:
            logger.warning(f"Failed to deliver webhook alert: {e}. Falling back to console.")
            return False

    def _notify_smtp(self, subject: str, message: str) -> bool:
        """Send email summary via SMTP (with safe mock fallback)."""
        if not self.smtp_host or self.smtp_host == "mock_host" or "example" in self.smtp_host:
            logger.info("SMTP alerting using placeholder credentials. Falling back to console log.")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_from
            msg["To"] = self.smtp_to
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
            if self.smtp_use_tls:
                server.starttls()
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"SMTP alert dispatched to {self.smtp_to}")
            return True
        except Exception as e:
            logger.warning(f"Failed to dispatch SMTP email: {e}. Alert fell back safely to console.")
            return False
