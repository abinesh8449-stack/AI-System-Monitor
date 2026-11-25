import csv
import io
import sys
from pathlib import Path

# Ensure project root is in sys.path for direct execution
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import importlib

def _get_db_connection():
    try:
        db = importlib.import_module("database")
        return db.get_db_connection()
    except Exception as e:
        raise RuntimeError(f"Database module could not be loaded: {e}")

def get_db_connection():
    return _get_db_connection()

def generate_csv_report():
    """
    Generate CSV audit report containing monitoring snapshots,
    health assessments, and AI recommendations.
    Returns:
        StringIO buffer containing CSV data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            timestamp, cpu_percent, ram_percent, disk_percent, 
            network_status, network_upload_speed, network_download_speed,
            overall_status, ai_recommendation, is_alert_triggered
        FROM monitoring_history
        ORDER BY timestamp DESC
        LIMIT 1000
    """)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        "Timestamp",
        "CPU Usage (%)",
        "RAM Usage (%)",
        "Disk Usage (%)",
        "Network Status",
        "Upload Speed (KB/s)",
        "Download Speed (KB/s)",
        "Overall Health",
        "AI Recommendation",
        "Alert Triggered"
    ])

    # Write Data Rows
    for row in rows:
        writer.writerow([
            row["timestamp"],
            row["cpu_percent"],
            row["ram_percent"],
            row["disk_percent"],
            row["network_status"],
            row["network_upload_speed"],
            row["network_download_speed"],
            row["overall_status"],
            row["ai_recommendation"] or "N/A",
            "Yes" if row["is_alert_triggered"] == 1 else "No"
        ])

    output.seek(0)
    return output

if __name__ == '__main__':
    print("=" * 60)
    print("  CSV REPORT GENERATOR MODULE SELF-TEST")
    print("=" * 60)
    buf = generate_csv_report()
    content = buf.getvalue()
    lines = content.strip().split("\n")
    print(f"  Generated CSV Rows: {len(lines)} (Header + data)")
    print(f"  Header Sample     : {lines[0] if lines else 'Empty'}")
    print("=" * 60)
    print("CSV report generator self-test completed successfully!")
