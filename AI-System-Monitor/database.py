import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Ensure project root is in sys.path for direct execution
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import Config

def get_db_connection():
    """Create a thread-safe connection to the SQLite database."""
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(Config.DATABASE_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # High-performance write-ahead logging
    return conn

def init_db():
    """Initialize database tables, indexes, and seed default administrative user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Monitoring History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cpu_percent REAL NOT NULL,
            ram_percent REAL NOT NULL,
            disk_percent REAL NOT NULL,
            network_status TEXT NOT NULL,
            network_upload_speed REAL DEFAULT 0.0,
            network_download_speed REAL DEFAULT 0.0,
            overall_status TEXT NOT NULL,
            ai_recommendation TEXT,
            is_alert_triggered INTEGER DEFAULT 0
        )
    """)
    
    # 3. Alerts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resource TEXT NOT NULL,
            value REAL NOT NULL,
            severity TEXT NOT NULL,
            problem TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            email_status TEXT NOT NULL,
            is_recovered INTEGER DEFAULT 0,
            recovery_timestamp TIMESTAMP
        )
    """)
    
    # 4. AI Recommendations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            trigger_event TEXT NOT NULL,
            problem TEXT NOT NULL,
            severity TEXT NOT NULL,
            possible_cause TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            preventive_action TEXT NOT NULL
        )
    """)
    
    # 5. System Events Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            details TEXT
        )
    """)
    
    # Create indexes for optimal lookup performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_time ON monitoring_history(timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_status ON monitoring_history(overall_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_recovered ON alerts(is_recovered)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_time ON recommendations(timestamp DESC)")
    
    # Seed default administrator if not present
    cursor.execute("SELECT id FROM users WHERE username = ?", (Config.DEFAULT_ADMIN_USER,))
    if not cursor.fetchone():
        hashed = generate_password_hash(Config.DEFAULT_ADMIN_PASS, method='scrypt')
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (Config.DEFAULT_ADMIN_USER, hashed))
        cursor.execute("""
            INSERT INTO system_events (event_type, description, details)
            VALUES (?, ?, ?)
        """, ("SYSTEM_INIT", "Database initialized and admin user created", f"Username: {Config.DEFAULT_ADMIN_USER}"))
    
    conn.commit()
    conn.close()

# ----------------- User Authentication Helpers -----------------

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def verify_user(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None

# ----------------- Monitoring History Helpers -----------------

def save_monitoring_snapshot(metrics):
    """Persist periodic system snapshot to monitoring_history table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO monitoring_history (
            cpu_percent, ram_percent, disk_percent, network_status,
            network_upload_speed, network_download_speed, overall_status,
            ai_recommendation, is_alert_triggered
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metrics.get("cpu_percent", 0.0),
        metrics.get("ram_percent", 0.0),
        metrics.get("disk_percent", 0.0),
        metrics.get("network_status", "Unknown"),
        metrics.get("network_upload_speed", 0.0),
        metrics.get("network_download_speed", 0.0),
        metrics.get("overall_status", "HEALTHY"),
        metrics.get("ai_recommendation", ""),
        1 if metrics.get("overall_status") == "CRITICAL" else 0
    ))
    conn.commit()
    conn.close()

def get_recent_history(limit=20):
    """Get the latest N monitoring records for quick display."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM monitoring_history
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_filtered_history(search='', status='', start_date='', end_date='', page=1, per_page=15):
    """Query history records with flexible filtering and pagination."""
    conn = get_db_connection()
    conditions = []
    params = []
    
    if search:
        conditions.append("(ai_recommendation LIKE ? OR network_status LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
        
    if status and status.upper() != 'ALL':
        conditions.append("overall_status = ?")
        params.append(status.upper())
        
    if start_date:
        conditions.append("timestamp >= ?")
        params.append(f"{start_date} 00:00:00")
        
    if end_date:
        conditions.append("timestamp <= ?")
        params.append(f"{end_date} 23:59:59")
        
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    # Count total matching rows
    count_query = f"SELECT COUNT(*) as count FROM monitoring_history {where_clause}"
    total_count = conn.execute(count_query, params).fetchone()["count"]
    
    # Pagination
    offset = (page - 1) * per_page
    data_query = f"""
        SELECT * FROM monitoring_history
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    rows = conn.execute(data_query, params + [per_page, offset]).fetchall()
    conn.close()
    
    return [dict(row) for row in rows], total_count

def get_history_stats():
    """Calculate min, max, avg statistical aggregate metrics for reporting."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT 
            COUNT(*) as total_records,
            MIN(cpu_percent) as min_cpu, MAX(cpu_percent) as max_cpu, AVG(cpu_percent) as avg_cpu,
            MIN(ram_percent) as min_ram, MAX(ram_percent) as max_ram, AVG(ram_percent) as avg_ram,
            MIN(disk_percent) as min_disk, MAX(disk_percent) as max_disk, AVG(disk_percent) as avg_disk,
            AVG(network_upload_speed) as avg_upload,
            AVG(network_download_speed) as avg_download
        FROM monitoring_history
    """).fetchone()
    conn.close()
    if row and row["total_records"] > 0:
        return {
            "total_records": row["total_records"],
            "min_cpu": round(row["min_cpu"] or 0.0, 1),
            "max_cpu": round(row["max_cpu"] or 0.0, 1),
            "avg_cpu": round(row["avg_cpu"] or 0.0, 1),
            "min_ram": round(row["min_ram"] or 0.0, 1),
            "max_ram": round(row["max_ram"] or 0.0, 1),
            "avg_ram": round(row["avg_ram"] or 0.0, 1),
            "min_disk": round(row["min_disk"] or 0.0, 1),
            "max_disk": round(row["max_disk"] or 0.0, 1),
            "avg_disk": round(row["avg_disk"] or 0.0, 1),
            "avg_upload": round(row["avg_upload"] or 0.0, 2),
            "avg_download": round(row["avg_download"] or 0.0, 2)
        }
    return {
        "total_records": 0,
        "min_cpu": 0.0, "max_cpu": 0.0, "avg_cpu": 0.0,
        "min_ram": 0.0, "max_ram": 0.0, "avg_ram": 0.0,
        "min_disk": 0.0, "max_disk": 0.0, "avg_disk": 0.0,
        "avg_upload": 0.0, "avg_download": 0.0
    }

# ----------------- Alert Log Helpers -----------------

def save_alert(resource, value, severity, problem, recommendation, email_status="Disabled"):
    """Persist an alert log entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alerts (
            resource, value, severity, problem, recommendation, email_status, is_recovered
        ) VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (resource, value, severity, problem, recommendation, email_status))
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id

def get_recent_alerts(limit=50):
    """Retrieve recent alerts."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM alerts
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def mark_active_alerts_recovered(resource=None):
    """Mark unrecovered alerts as recovered upon system stabilization."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if resource:
        cursor.execute("""
            UPDATE alerts
            SET is_recovered = 1, recovery_timestamp = ?
            WHERE resource = ? AND is_recovered = 0
        """, (now_str, resource))
    else:
        cursor.execute("""
            UPDATE alerts
            SET is_recovered = 1, recovery_timestamp = ?
            WHERE is_recovered = 0
        """, (now_str,))
    updated_count = cursor.rowcount
    conn.commit()
    conn.close()
    return updated_count

def get_alert_counts():
    """Retrieve summary counts for alerts and recovery events."""
    conn = get_db_connection()
    total_alerts = conn.execute("SELECT COUNT(*) as cnt FROM alerts").fetchone()["cnt"]
    critical_alerts = conn.execute("SELECT COUNT(*) as cnt FROM alerts WHERE severity = 'CRITICAL'").fetchone()["cnt"]
    warning_alerts = conn.execute("SELECT COUNT(*) as cnt FROM alerts WHERE severity = 'WARNING'").fetchone()["cnt"]
    recovered_events = conn.execute("SELECT COUNT(*) as cnt FROM alerts WHERE is_recovered = 1").fetchone()["cnt"]
    last_alert = conn.execute("SELECT timestamp, resource, severity FROM alerts ORDER BY timestamp DESC LIMIT 1").fetchone()
    conn.close()
    return {
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "warning_alerts": warning_alerts,
        "recovered_events": recovered_events,
        "last_alert": dict(last_alert) if last_alert else None
    }

# ----------------- AI Recommendations Helpers -----------------

def save_recommendation(rec):
    """Persist generated AI recommendation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO recommendations (
            status, trigger_event, problem, severity, possible_cause, recommended_action, preventive_action
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        rec.get("status", "HEALTHY"),
        rec.get("trigger_event", "Periodic Evaluation"),
        rec.get("problem", ""),
        rec.get("severity", "HEALTHY"),
        rec.get("possible_cause", ""),
        rec.get("recommended_action", ""),
        rec.get("preventive_action", "")
    ))
    conn.commit()
    conn.close()

def get_latest_recommendation():
    """Get the most recent AI recommendation record."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT * FROM recommendations
        ORDER BY timestamp DESC
        LIMIT 1
    """).fetchone()
    conn.close()
    return dict(row) if row else None

# ----------------- System Events Helpers -----------------

def log_system_event(event_type, description, details=None):
    """Log an operational lifecycle event."""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO system_events (event_type, description, details)
        VALUES (?, ?, ?)
    """, (event_type, description, details))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("  DATABASE MODULE SELF-TEST")
    print("=" * 60)
    init_db()
    stats = get_history_stats()
    alerts = get_alert_counts()
    print(f"  Database Path   : {Config.DATABASE_PATH}")
    print(f"  Total Snapshots : {stats['total_records']}")
    print(f"  Total Alerts    : {alerts['total_alerts']} (Critical: {alerts['critical_alerts']}, Recovered: {alerts['recovered_events']})")
    print("=" * 60)
    print("Database self-test completed successfully!")
