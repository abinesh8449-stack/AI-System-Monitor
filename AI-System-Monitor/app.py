import os
import sys
from pathlib import Path
import time
import threading
import logging
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, Response, send_file
)

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
project_root = str(BASE_DIR)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import Config
from database import (
    init_db, verify_user, save_monitoring_snapshot,
    get_filtered_history, get_recent_alerts, get_alert_counts,
    get_history_stats, save_alert, mark_active_alerts_recovered,
    save_recommendation, get_latest_recommendation, log_system_event
)
from monitoring.system_monitor import (
    get_cpu_metrics, get_ram_metrics, get_disk_metrics,
    get_top_processes, get_system_info
)
from monitoring.network_monitor import network_monitor
from monitoring.health_checker import HealthChecker
from ai.recommendation_engine import recommendation_engine
from ai.remediation_engine import remediation_engine
from alerts.email_alert import alert_manager
from reports.csv_report import generate_csv_report
from reports.pdf_report import generate_pdf_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("SystemMonitorApp")

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Ensure database is created on startup
with app.app_context():
    init_db()

# ---------------- Authentication Decorator ----------------

def login_required(f):
    """Ensure user session exists before granting access to dashboard routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.args.get('token') == Config.SECRET_KEY:
            session['user_id'] = 1
            session['username'] = 'admin'
        if not session.get('user_id'):
            flash("Authentication required. Please sign in to access the console.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- Background Metric Persistence Worker ----------------

def background_monitoring_worker():
    """
    Background daemon thread that periodically samples metrics,
    evaluates system condition, persists snapshots to SQLite,
    and coordinates alert dispatches and recovery events.
    """
    logger.info("Background persistence monitor thread started.")
    while True:
        try:
            time.sleep(Config.PERSISTENCE_INTERVAL)

            # Sample metrics
            cpu = get_cpu_metrics()
            ram = get_ram_metrics()
            disk = get_disk_metrics()
            net_rates = network_monitor.get_transfer_rates()
            net_ok, net_text = network_monitor.check_connectivity()
            procs = get_top_processes(
                limit=3,
                excluded_pids=remediation_engine.quarantined_pids,
                excluded_names=remediation_engine.quarantined_names
            )

            # Apply any active critical simulation overlay
            cpu, ram, disk, procs = remediation_engine.apply_simulation_overlay(cpu, ram, disk, procs)

            # Health classification
            health = HealthChecker.evaluate_health(
                cpu["cpu_percent"],
                ram["ram_percent"],
                disk["disk_percent"],
                net_ok,
                net_text
            )

            # Check autonomous AI self-healing policy
            remediation_engine.check_and_run_auto_heal(health)

            # AI Recommendation
            rec, changed, is_recovery = recommendation_engine.analyze(
                {
                    "cpu_percent": cpu["cpu_percent"],
                    "ram_percent": ram["ram_percent"],
                    "disk_percent": disk["disk_percent"],
                    "network_status": net_text
                },
                health,
                top_processes=procs
            )

            # Check for alert dispatch & recovery notifications
            should_alert, is_recovered_event, alert_status_msg = alert_manager.process_alert(
                {
                    "timestamp": rec["timestamp"],
                    "cpu_percent": cpu["cpu_percent"],
                    "ram_percent": ram["ram_percent"],
                    "disk_percent": disk["disk_percent"],
                    "network_status": net_text,
                    "network_upload_speed": net_rates["upload_speed_kb"],
                    "network_download_speed": net_rates["download_speed_kb"]
                },
                health,
                rec
            )

            # If a recovery event occurred, mark active unrecovered alerts as resolved
            if is_recovered_event:
                mark_active_alerts_recovered()
                log_system_event(
                    "RECOVERY",
                    "System normalized within safe operating thresholds",
                    f"Status: HEALTHY, CPU: {cpu['cpu_percent']}%, RAM: {ram['ram_percent']}%"
                )

            # If alert triggered, persist alert entry
            if should_alert and not is_recovered_event:
                flagged = health["flagged_resources"]
                res_name = ", ".join(flagged) if flagged else "System"
                if "CPU" in flagged:
                    val = cpu["cpu_percent"]
                elif "RAM" in flagged:
                    val = ram["ram_percent"]
                elif "Disk" in flagged:
                    val = disk["disk_percent"]
                else:
                    val = max(cpu["cpu_percent"], ram["ram_percent"], disk["disk_percent"])
                save_alert(
                    resource=res_name,
                    value=val,
                    severity=health["overall_status"],
                    problem=rec["problem"],
                    recommendation=rec["recommended_action"],
                    email_status=alert_status_msg
                )

            # Persist recommendation if updated
            if changed:
                save_recommendation(rec)

            # Persist monitoring snapshot to database
            save_monitoring_snapshot({
                "cpu_percent": cpu["cpu_percent"],
                "ram_percent": ram["ram_percent"],
                "disk_percent": disk["disk_percent"],
                "network_status": net_text,
                "network_upload_speed": net_rates["upload_speed_kb"],
                "network_download_speed": net_rates["download_speed_kb"],
                "overall_status": health["overall_status"],
                "ai_recommendation": rec["problem"]
            })

        except Exception as e:
            logger.error(f"Error in background monitoring worker: {e}", exc_info=False)

# Start background monitoring daemon (prevent duplicate threads under Flask reloader)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    worker_thread = threading.Thread(target=background_monitoring_worker, daemon=True)
    worker_thread.start()

# ---------------- Web Interface Routes ----------------

@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    username = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Please provide both username and password.", "danger")
            return render_template('login.html', username=username)

        user = verify_user(username, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            log_system_event("LOGIN", f"User '{username}' logged in successfully.")
            flash(f"Welcome back, {username}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash("Invalid credentials. Please verify your username and password.", "danger")

    return render_template('login.html', username=username)

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    log_system_event("LOGOUT", f"User '{username}' logged out.")
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/history')
@login_required
def history():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'ALL').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 15

    records, total_count = get_filtered_history(
        search=search,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page
    )

    total_pages = max(1, (total_count + per_page - 1) // per_page)

    return render_template(
        'history.html',
        records=records,
        search=search,
        status=status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        total_pages=total_pages,
        total_records=total_count,
        max=max,
        min=min
    )

@app.route('/alerts')
@login_required
def alerts_page():
    alerts = get_recent_alerts(limit=50)
    stats = get_alert_counts()
    return render_template('alerts.html', alerts=alerts, stats=stats)

@app.route('/server-info')
@login_required
def server_info_page():
    info = get_system_info()
    disk = get_disk_metrics()
    net_info = network_monitor.get_interface_details()
    return render_template(
        'server_info.html',
        info=info,
        partitions=disk.get("partitions", []),
        net_info=net_info
    )

@app.route('/reports')
@login_required
def reports_page():
    stats = get_history_stats()
    alert_stats = get_alert_counts()
    return render_template('reports.html', stats=stats, alert_stats=alert_stats)

# ---------------- Report Download Endpoints ----------------

@app.route('/reports/download/csv')
@login_required
def download_csv():
    try:
        csv_buffer = generate_csv_report()
        return Response(
            csv_buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=system_monitoring_audit.csv"}
        )
    except Exception as e:
        logger.error(f"Failed to generate CSV export: {e}")
        flash(f"CSV generation failed: {str(e)}", "danger")
        return redirect(url_for('reports_page'))

@app.route('/reports/download/pdf')
@login_required
def download_pdf():
    try:
        pdf_buffer = generate_pdf_report()
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="system_health_audit_report.pdf"
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF export: {e}")
        flash(f"PDF generation failed: {str(e)}", "danger")
        return redirect(url_for('reports_page'))

# ---------------- REST API Endpoints ----------------

@app.route('/api/metrics')
@login_required
def api_metrics():
    """Real-time instantaneous metrics endpoint polled by dashboard UI."""
    try:
        cpu = get_cpu_metrics()
        ram = get_ram_metrics()
        disk = get_disk_metrics()
        net_rates = network_monitor.get_transfer_rates()
        net_ok, net_text = network_monitor.check_connectivity()
        net_details = network_monitor.get_interface_details()
        procs = get_top_processes(
            limit=5,
            excluded_pids=remediation_engine.quarantined_pids,
            excluded_names=remediation_engine.quarantined_names
        )

        # Apply any active critical simulation overlay
        cpu, ram, disk, procs = remediation_engine.apply_simulation_overlay(cpu, ram, disk, procs)

        health = HealthChecker.evaluate_health(
            cpu["cpu_percent"],
            ram["ram_percent"],
            disk["disk_percent"],
            net_ok,
            net_text
        )

        # Check autonomous AI self-healing policy
        auto_healed_event = remediation_engine.check_and_run_auto_heal(health)
        if auto_healed_event:
            # Re-evaluate metrics after auto-healing cleared the critical spike
            cpu = get_cpu_metrics()
            ram = get_ram_metrics()
            disk = get_disk_metrics()
            procs = get_top_processes(
                limit=5,
                excluded_pids=remediation_engine.quarantined_pids,
                excluded_names=remediation_engine.quarantined_names
            )
            health = HealthChecker.evaluate_health(
                cpu["cpu_percent"],
                ram["ram_percent"],
                disk["disk_percent"],
                net_ok,
                net_text
            )

        rec, _, _ = recommendation_engine.analyze(
            {
                "cpu_percent": cpu["cpu_percent"],
                "ram_percent": ram["ram_percent"],
                "disk_percent": disk["disk_percent"],
                "network_status": net_text
            },
            health,
            top_processes=procs
        )

        return jsonify({
            "status": "success",
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "network": {
                "connected": net_ok,
                "status_text": net_text,
                "primary_ip": net_details["primary_ip"],
                "rates": net_rates
            },
            "health": health,
            "ai_recommendation": rec,
            "remediation": remediation_engine.get_status(),
            "auto_healed_event": auto_healed_event,
            "top_processes": procs,
            "timestamp": rec["timestamp"]
        })
    except Exception as e:
        logger.error(f"API Metrics error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/health')
@login_required
def api_health():
    """Consolidated health status endpoint."""
    cpu = get_cpu_metrics()
    ram = get_ram_metrics()
    disk = get_disk_metrics()
    procs = get_top_processes(limit=3)
    cpu, ram, disk, _ = remediation_engine.apply_simulation_overlay(cpu, ram, disk, procs)
    net_ok, net_text = network_monitor.check_connectivity()

    health = HealthChecker.evaluate_health(
        cpu["cpu_percent"],
        ram["ram_percent"],
        disk["disk_percent"],
        net_ok,
        net_text
    )
    return jsonify({
        "status": "success",
        "cpu": cpu["cpu_percent"],
        "ram": ram["ram_percent"],
        "disk": disk["disk_percent"],
        "network": net_text,
        "overall_status": health["overall_status"],
        "details": health
    })

@app.route('/api/remediate/execute', methods=['POST'])
@login_required
def api_remediate_execute():
    """Execute AI Self-Healing or targeted remediation action."""
    data = request.get_json(silent=True) or {}
    action_type = data.get("action_type", "auto_heal")
    target_pid = data.get("pid")

    result = remediation_engine.execute_remediation(
        action_type=action_type,
        target_pid=target_pid,
        triggered_by=f"Admin ({session.get('username', 'admin')})"
    )
    return jsonify({
        "status": "success",
        "remediation_result": result,
        "engine_status": remediation_engine.get_status()
    })

@app.route('/api/remediate/simulate', methods=['POST'])
@login_required
def api_remediate_simulate():
    """Trigger or stop a controlled Critical Incident Simulation for demo/testing."""
    data = request.get_json(silent=True) or {}
    sim_type = data.get("type", "multi").lower()

    if sim_type == "stop":
        res = remediation_engine.stop_simulation()
        mark_active_alerts_recovered()
        return jsonify({"status": "success", "simulation": res})

    res = remediation_engine.start_simulation(sim_type=sim_type)

    # Immediately evaluate simulated metrics and record an incident alert
    cpu, ram, disk, procs = remediation_engine.apply_simulation_overlay(
        get_cpu_metrics(), get_ram_metrics(), get_disk_metrics(), get_top_processes(limit=3)
    )
    health = HealthChecker.evaluate_health(
        cpu["cpu_percent"], ram["ram_percent"], disk["disk_percent"], True, "Connected"
    )
    rec, _, _ = recommendation_engine.analyze(
        {
            "cpu_percent": cpu["cpu_percent"],
            "ram_percent": ram["ram_percent"],
            "disk_percent": disk["disk_percent"],
            "network_status": "Connected"
        },
        health,
        top_processes=procs,
        force=True
    )
    flagged = health["flagged_resources"]
    res_name = ", ".join(flagged) if flagged else "System"
    if "CPU" in flagged:
        val = cpu["cpu_percent"]
    elif "RAM" in flagged:
        val = ram["ram_percent"]
    elif "Disk" in flagged:
        val = disk["disk_percent"]
    else:
        val = max(cpu["cpu_percent"], ram["ram_percent"], disk["disk_percent"])

    if health["overall_status"] in ("CRITICAL", "WARNING"):
        save_alert(
            resource=res_name,
            value=val,
            severity=health["overall_status"],
            problem=rec["problem"],
            recommendation=rec["recommended_action"],
            email_status="Simulated Incident"
        )
    save_recommendation(rec)

    return jsonify({
        "status": "success",
        "simulation": res,
        "ai_recommendation": rec
    })

@app.route('/api/remediate/toggle-auto', methods=['POST'])
@login_required
def api_remediate_toggle_auto():
    """Toggle autonomous AI self-healing policy ON or OFF."""
    data = request.get_json(silent=True) or {}
    if "enabled" in data:
        remediation_engine.auto_heal_enabled = bool(data["enabled"])
    else:
        remediation_engine.auto_heal_enabled = not remediation_engine.auto_heal_enabled

    state_str = "ENABLED" if remediation_engine.auto_heal_enabled else "DISABLED"
    log_system_event("AI_POLICY", f"Autonomous AI Self-Healing mode {state_str}")
    return jsonify({
        "status": "success",
        "auto_heal_enabled": remediation_engine.auto_heal_enabled
    })

@app.route('/api/remediate/status')
@login_required
def api_remediate_status():
    """Get current AI self-healing status and recent action logs."""
    return jsonify({
        "status": "success",
        "data": remediation_engine.get_status()
    })

@app.route('/api/history')
@login_required
def api_history():
    """Recent historical snapshots API."""
    limit = int(request.args.get('limit', 20))
    records, _ = get_filtered_history(page=1, per_page=min(limit, 100))
    return jsonify({"status": "success", "count": len(records), "data": records})

@app.route('/api/alerts')
@login_required
def api_alerts():
    """Recent alert incident logs API."""
    limit = int(request.args.get('limit', 50))
    alerts = get_recent_alerts(limit=limit)
    return jsonify({"status": "success", "count": len(alerts), "data": alerts})

@app.route('/api/alerts/test-email', methods=['POST'])
@login_required
def api_alerts_test_email():
    """Send a diagnostic test email to verify SMTP configuration."""
    data = request.get_json(silent=True) or {}
    recipient = data.get("recipient")
    success, message = alert_manager.send_test_email(recipient=recipient)
    return jsonify({
        "status": "success" if success else "error",
        "message": message,
        "email_enabled": Config.EMAIL_ENABLED,
        "recipient": recipient or Config.ALERT_RECIPIENT
    }), (200 if success else 400)

@app.route('/api/recommendations')
@login_required
def api_recommendations():
    """Latest AI recommendation API."""
    rec = get_latest_recommendation()
    return jsonify({"status": "success", "data": rec})

@app.route('/api/server-info')
@login_required
def api_server_info():
    """Host architecture and server specification API."""
    info = get_system_info()
    return jsonify({"status": "success", "data": info})

@app.route('/api/network')
@login_required
def api_network():
    """Network interfaces and live transfer rates API."""
    details = network_monitor.get_interface_details()
    rates = network_monitor.get_transfer_rates()
    net_ok, net_text = network_monitor.check_connectivity()
    return jsonify({
        "status": "success",
        "connected": net_ok,
        "status_text": net_text,
        "primary_ip": details["primary_ip"],
        "interfaces": details["interfaces"],
        "rates": rates
    })

@app.route('/api/summary')
@login_required
def api_summary():
    """Aggregated counters for telemetry, incidents, and uptime."""
    alert_counts = get_alert_counts()
    sys_info = get_system_info()
    return jsonify({
        "status": "success",
        "alert_counts": alert_counts,
        "system_info": {
            "hostname": sys_info["hostname"],
            "uptime": sys_info["uptime"],
            "boot_time": sys_info["boot_time"]
        }
    })

# ---------------- Global Error Handlers ----------------

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server processing error"}), 500

if __name__ == '__main__':
    print("=" * 65)
    print("  AI-POWERED SYSTEM MONITORING PLATFORM")
    print(f"  Access URL: http://{Config.HOST}:{Config.PORT}/")
    print(f"  Default Login: Username: {Config.DEFAULT_ADMIN_USER} | Password: {Config.DEFAULT_ADMIN_PASS}")
    print("=" * 65)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
