import smtplib
import time
import logging
import sys
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Ensure project root is in sys.path for direct execution
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import importlib

def _resolve_config():
    try:
        return importlib.import_module("config").Config
    except Exception:
        class _FallbackConfig:
            ALERT_COOLDOWN_SECONDS = 300
            EMAIL_ENABLED = False
            EMAIL_HOST = "smtp.gmail.com"
            EMAIL_PORT = 587
            EMAIL_USE_TLS = True
            EMAIL_USERNAME = ""
            EMAIL_PASSWORD = ""
            ALERT_RECIPIENT = ""
            HOST = "127.0.0.1"
            PORT = 5000
            CPU_CRITICAL = 80.0
            RAM_CRITICAL = 80.0
            DISK_CRITICAL = 85.0
        return _FallbackConfig

Config = _resolve_config()

logger = logging.getLogger(__name__)

class AlertManager:
    """
    Manages alerting logic, anti-spam cooldown mechanisms, and SMTP email dispatch.
    """

    def __init__(self):
        self._last_alert_time: float = 0.0
        self._is_in_critical_state: bool = False
        self._last_severity: str = "HEALTHY"

    def process_alert(self, metrics, health_eval, recommendation):
        """
        Evaluate whether an alert or recovery notification should be sent.
        Returns a tuple: (should_alert, is_recovery, status_message)
        """
        overall_status = health_eval["overall_status"]
        current_time = time.time()
        cooldown_elapsed = (current_time - self._last_alert_time) >= Config.ALERT_COOLDOWN_SECONDS

        # 1. Detect Recovery (only when health safely normalizes back to HEALTHY)
        if self._is_in_critical_state and overall_status == "HEALTHY":
            self._is_in_critical_state = False
            self._last_severity = "HEALTHY"
            
            # Send recovery notification
            status_msg = self._send_recovery_email(metrics, recommendation)
            return True, True, status_msg

        # 2. Detect Transition into CRITICAL or Cooldown Expiration in CRITICAL
        if overall_status == "CRITICAL":
            if not self._is_in_critical_state or cooldown_elapsed:
                self._is_in_critical_state = True
                self._last_severity = "CRITICAL"
                self._last_alert_time = current_time

                status_msg = self._send_critical_email(metrics, health_eval, recommendation)
                return True, False, status_msg
            else:
                return False, False, "Suppressed (Cooldown active)"

        self._last_severity = overall_status
        return False, False, "No Alert Required"

    def send_test_email(self, recipient=None):
        """
        Send a test email to verify SMTP configuration and connectivity.
        Returns a tuple: (success: bool, message: str)
        """
        if not Config.EMAIL_ENABLED:
            return False, "Email alerts are disabled in configuration (.env: EMAIL_ENABLED=False)"

        target = recipient or Config.ALERT_RECIPIENT
        if not Config.EMAIL_USERNAME or not target:
            return False, "Missing SMTP credentials or recipient in configuration (.env)"

        subject = f"[TEST] AI System Monitor - SMTP Verification - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body_text = f"""
=====================================================
AI-POWERED SYSTEM MONITORING PLATFORM
SMTP VERIFICATION TEST
=====================================================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: VERIFICATION SUCCESSFUL

This is an automated test notification confirming that
SMTP mail delivery is operating properly.

Host: {Config.EMAIL_HOST}:{Config.EMAIL_PORT}
Sender: {Config.EMAIL_USERNAME}
Target: {target}
Dashboard URL: http://{Config.HOST}:{Config.PORT}/
=====================================================
"""
        status_msg = self._dispatch_email(subject, body_text)
        if "Sent" in status_msg:
            return True, f"Test email successfully dispatched to {target}"
        return False, f"Email delivery failed: {status_msg}"

    def _send_critical_email(self, metrics, health_eval, recommendation):
        """Construct and send critical threshold alert email."""
        if not Config.EMAIL_ENABLED:
            logger.info("Email alerts disabled in configuration. Alert logged locally.")
            return "Disabled (Configured in .env)"

        subject = f"[CRITICAL ALERT] System Monitoring Platform - {metrics.get('timestamp')}"
        
        body_text = f"""
=====================================================
CRITICAL SYSTEM HEALTH ALERT
=====================================================
Timestamp: {metrics.get('timestamp')}
Overall Status: CRITICAL

CURRENT SYSTEM METRICS:
- CPU Utilization: {metrics.get('cpu_percent')}% (Threshold: {Config.CPU_CRITICAL}%)
- RAM Utilization: {metrics.get('ram_percent')}% (Threshold: {Config.RAM_CRITICAL}%)
- Disk Utilization: {metrics.get('disk_percent')}% (Threshold: {Config.DISK_CRITICAL}%)
- Network Status: {metrics.get('network_status')}
- Network Upload: {metrics.get('network_upload_speed', 0.0)} KB/s
- Network Download: {metrics.get('network_download_speed', 0.0)} KB/s

AI DIAGNOSTIC RECOMMENDATION:
- Problem: {recommendation.get('problem')}
- Possible Cause: {recommendation.get('possible_cause')}
- Recommended Action: {recommendation.get('recommended_action')}
- Preventive Action: {recommendation.get('preventive_action')}

Please inspect the system dashboard immediately:
http://{Config.HOST}:{Config.PORT}/dashboard
=====================================================
        """

        return self._dispatch_email(subject, body_text)

    def _send_recovery_email(self, metrics, recommendation):
        """Construct and send system recovery notification email."""
        if not Config.EMAIL_ENABLED:
            return "Disabled"

        subject = f"[RECOVERED] System Health Stabilized - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body_text = f"""
=====================================================
SYSTEM HEALTH RECOVERY NOTIFICATION
=====================================================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Overall Status: NORMALIZED (HEALTHY)

CURRENT METRICS:
- CPU Utilization: {metrics.get('cpu_percent')}%
- RAM Utilization: {metrics.get('ram_percent')}%
- Disk Utilization: {metrics.get('disk_percent')}%
- Network: {metrics.get('network_status')}

AI OBSERVATION:
{recommendation.get('problem')}
The system has safely returned to normal operating parameters.
=====================================================
        """
        return self._dispatch_email(subject, body_text)

    def _dispatch_email(self, subject, body_text):
        """Internal worker to dispatch email via SMTP."""
        if not Config.EMAIL_USERNAME or not Config.ALERT_RECIPIENT:
            logger.warning("SMTP credentials or recipient missing. Cannot send email.")
            return "Failed: Missing SMTP credentials"

        try:
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_USERNAME
            msg['To'] = Config.ALERT_RECIPIENT
            msg['Subject'] = subject
            msg.attach(MIMEText(body_text, 'plain'))

            server = smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT, timeout=10)
            if Config.EMAIL_USE_TLS:
                server.starttls()
            if Config.EMAIL_PASSWORD:
                server.login(Config.EMAIL_USERNAME, Config.EMAIL_PASSWORD)
            
            server.send_message(msg)
            server.quit()
            logger.info(f"Alert email successfully delivered to {Config.ALERT_RECIPIENT}")
            return "Sent"
        except Exception as e:
            logger.error(f"Failed to send email alert via SMTP: {str(e)}")
            return f"Failed: {str(e)[:50]}"

# Global singleton alert manager
alert_manager = AlertManager()

if __name__ == '__main__':
    print("=" * 65)
    print("  AI-POWERED SYSTEM MONITORING PLATFORM - ALERT MANAGER TEST")
    print("=" * 65)
    print(f"  Email Enabled   : {Config.EMAIL_ENABLED}")
    print(f"  SMTP Host       : {Config.EMAIL_HOST}:{Config.EMAIL_PORT}")
    print(f"  SMTP Username   : {Config.EMAIL_USERNAME or '(Not configured in .env)'}")
    print(f"  Alert Recipient : {Config.ALERT_RECIPIENT or '(Not configured in .env)'}")
    print(f"  Alert Cooldown  : {Config.ALERT_COOLDOWN_SECONDS}s")
    print("-" * 65)

    test_metrics = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent": 94.2,
        "ram_percent": 89.5,
        "disk_percent": 72.0,
        "network_status": "Connected",
        "network_upload_speed": 14.5,
        "network_download_speed": 52.3
    }
    test_health = {
        "overall_status": "CRITICAL",
        "cpu_status": "CRITICAL",
        "ram_status": "CRITICAL",
        "disk_status": "WARNING",
        "network_status": "HEALTHY",
        "flagged_resources": ["CPU", "RAM"]
    }
    test_rec = {
        "timestamp": test_metrics["timestamp"],
        "problem": "Severe CPU & RAM Saturation Detected (CPU 94.2%, RAM 89.5%)",
        "possible_cause": "High-intensity computational workload or memory leak.",
        "recommended_action": "Inspect active process tree and isolate runaway workers.",
        "preventive_action": "Configure process resource quotas and monitor headroom."
    }

    print("\n[Test 1] Processing CRITICAL event:")
    should_alert, is_rec, status_msg = alert_manager.process_alert(test_metrics, test_health, test_rec)
    print(f"  -> Should Alert: {should_alert}")
    print(f"  -> Is Recovery : {is_rec}")
    print(f"  -> Status Msg  : {status_msg}")

    print("\n[Test 2] Processing subsequent event within cooldown window:")
    should_alert2, is_rec2, status_msg2 = alert_manager.process_alert(test_metrics, test_health, test_rec)
    print(f"  -> Should Alert: {should_alert2}")
    print(f"  -> Is Recovery : {is_rec2}")
    print(f"  -> Status Msg  : {status_msg2}")

    print("\n[Test 3] Processing RECOVERY event (health stabilized to HEALTHY):")
    test_health_rec = {
        "overall_status": "HEALTHY",
        "cpu_status": "HEALTHY",
        "ram_status": "HEALTHY",
        "disk_status": "HEALTHY",
        "network_status": "HEALTHY",
        "flagged_resources": []
    }
    test_rec_rec = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "problem": "System telemetry normalized within safe operational thresholds.",
        "recommended_action": "Maintain normal continuous monitoring."
    }
    should_alert3, is_rec3, status_msg3 = alert_manager.process_alert(test_metrics, test_health_rec, test_rec_rec)
    print(f"  -> Should Alert: {should_alert3}")
    print(f"  -> Is Recovery : {is_rec3}")
    print(f"  -> Status Msg  : {status_msg3}")

    print("\n" + "=" * 65)
    print("AlertManager module self-test completed successfully!")
    print("=" * 65)
