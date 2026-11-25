import io
import sys
from typing import List
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib import colors  # type: ignore
from reportlab.platypus import (  # type: ignore
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore

# Ensure project root is in sys.path for direct execution
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import importlib

def _get_db():
    return importlib.import_module("database")

def _get_sys_monitor():
    return importlib.import_module("monitoring.system_monitor")

def get_db_connection():
    return _get_db().get_db_connection()

def get_history_stats():
    return _get_db().get_history_stats()

def get_alert_counts():
    return _get_db().get_alert_counts()

def get_system_info():
    return _get_sys_monitor().get_system_info()

def generate_pdf_report():
    """
    Generate an academic/enterprise-grade PDF system health report
    using ReportLab and return an in-memory BytesIO buffer.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story: List[Flowable] = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=1  # Center
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#2563eb'),
        alignment=1
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=6
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )

    header_cell_style = ParagraphStyle(
        'TableHeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    # 1. Title & Header
    story.append(Paragraph("AI-POWERED SYSTEM MONITORING PLATFORM", title_style))
    story.append(Paragraph("Comprehensive Hardware & System Health Audit Report", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=10))

    # Meta bar
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_text = f"<b>Generated:</b> {gen_time} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Report Type:</b> Full Diagnostic & Performance Audit"
    story.append(Paragraph(meta_text, cell_style))
    story.append(Spacer(1, 10))

    # 2. Server Specifications Section
    sys_info = get_system_info()
    story.append(Paragraph("1. Host Server Specifications", section_heading))
    
    server_data = [
        [Paragraph("<b>Operating System:</b>", cell_style), Paragraph(f"{sys_info.get('os_name')} {sys_info.get('os_release')}", cell_style),
         Paragraph("<b>Hostname:</b>", cell_style), Paragraph(f"{sys_info.get('hostname')}", cell_style)],
        [Paragraph("<b>Processor:</b>", cell_style), Paragraph(f"{sys_info.get('processor')[:30]}", cell_style),
         Paragraph("<b>CPU Cores:</b>", cell_style), Paragraph(f"{sys_info.get('cpu_physical_cores')} Physical / {sys_info.get('cpu_logical_cores')} Logical", cell_style)],
        [Paragraph("<b>Total Memory:</b>", cell_style), Paragraph(f"{sys_info.get('total_ram_gb')} GB", cell_style),
         Paragraph("<b>Primary Storage:</b>", cell_style), Paragraph(f"{sys_info.get('total_disk_gb')} GB", cell_style)],
        [Paragraph("<b>System Uptime:</b>", cell_style), Paragraph(f"{sys_info.get('uptime')}", cell_style),
         Paragraph("<b>Python Runtime:</b>", cell_style), Paragraph(f"{sys_info.get('python_version')}", cell_style)]
    ]
    server_table = Table(server_data, colWidths=[100, 170, 90, 180])
    server_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(server_table)
    story.append(Spacer(1, 12))

    # 3. Statistical Analysis Section
    stats = get_history_stats()
    alert_counts = get_alert_counts()
    story.append(Paragraph("2. Performance Aggregates & Health Summary", section_heading))

    stat_data = [
        [Paragraph("<b>Resource</b>", header_cell_style), 
         Paragraph("<b>Minimum</b>", header_cell_style), 
         Paragraph("<b>Average</b>", header_cell_style), 
         Paragraph("<b>Maximum</b>", header_cell_style),
         Paragraph("<b>Observed Alert Events</b>", header_cell_style)],
        [Paragraph("CPU Utilization", cell_style), Paragraph(f"{stats['min_cpu']}%", cell_style), Paragraph(f"{stats['avg_cpu']}%", cell_style), Paragraph(f"{stats['max_cpu']}%", cell_style), Paragraph(f"Critical: {alert_counts['critical_alerts']}", cell_style)],
        [Paragraph("RAM Utilization", cell_style), Paragraph(f"{stats['min_ram']}%", cell_style), Paragraph(f"{stats['avg_ram']}%", cell_style), Paragraph(f"{stats['max_ram']}%", cell_style), Paragraph(f"Warning: {alert_counts['warning_alerts']}", cell_style)],
        [Paragraph("Disk Utilization", cell_style), Paragraph(f"{stats['min_disk']}%", cell_style), Paragraph(f"{stats['avg_disk']}%", cell_style), Paragraph(f"{stats['max_disk']}%", cell_style), Paragraph(f"Recovered: {alert_counts['recovered_events']}", cell_style)],
        [Paragraph("Network Activity", cell_style), Paragraph("0.0 KB/s", cell_style), Paragraph(f"Up: {stats['avg_upload']} / Down: {stats['avg_download']} KB/s", cell_style), Paragraph("Dynamic", cell_style), Paragraph(f"Total Alerts: {alert_counts['total_alerts']}", cell_style)]
    ]
    stat_table = Table(stat_data, colWidths=[120, 95, 125, 95, 105])
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 12))

    # 4. Recent Alerts & AI Recommendations
    story.append(Paragraph("3. Recent Critical Alerts & AI Recommendations", section_heading))
    conn = get_db_connection()
    alerts = conn.execute("""
        SELECT timestamp, resource, value, severity, problem, recommendation, is_recovered
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT 6
    """).fetchall()

    if alerts:
        alert_table_data = [[
            Paragraph("<b>Timestamp</b>", header_cell_style),
            Paragraph("<b>Resource</b>", header_cell_style),
            Paragraph("<b>Value</b>", header_cell_style),
            Paragraph("<b>Severity</b>", header_cell_style),
            Paragraph("<b>Problem & AI Recommendation</b>", header_cell_style),
            Paragraph("<b>Recovery</b>", header_cell_style)
        ]]
        for a in alerts:
            rec_snippet = f"<b>{a['problem']}</b><br/>{a['recommendation'][:120]}..."
            status_text = "Recovered" if a["is_recovered"] == 1 else "Active / Pending"
            alert_table_data.append([
                Paragraph(a["timestamp"], cell_style),
                Paragraph(a["resource"], cell_style),
                Paragraph(f"{a['value']}%", cell_style),
                Paragraph(a["severity"], cell_style),
                Paragraph(rec_snippet, cell_style),
                Paragraph(status_text, cell_style)
            ])
        alert_table = Table(alert_table_data, colWidths=[90, 50, 45, 55, 230, 70])
        alert_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#b91c1c')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff1f2')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(alert_table)
    else:
        story.append(Paragraph("<i>No critical alerts recorded. System operated stably.</i>", cell_style))
    story.append(Spacer(1, 12))

    # 5. Recent System Monitoring Snapshots
    story.append(Paragraph("4. Historical Monitoring Snapshot Log", section_heading))
    history_rows = conn.execute("""
        SELECT timestamp, cpu_percent, ram_percent, disk_percent, network_status, overall_status
        FROM monitoring_history
        ORDER BY timestamp DESC
        LIMIT 10
    """).fetchall()
    conn.close()

    if history_rows:
        hist_table_data = [[
            Paragraph("<b>Timestamp</b>", header_cell_style),
            Paragraph("<b>CPU (%)</b>", header_cell_style),
            Paragraph("<b>RAM (%)</b>", header_cell_style),
            Paragraph("<b>Disk (%)</b>", header_cell_style),
            Paragraph("<b>Network</b>", header_cell_style),
            Paragraph("<b>Overall Health</b>", header_cell_style)
        ]]
        for h in history_rows:
            hist_table_data.append([
                Paragraph(h["timestamp"], cell_style),
                Paragraph(f"{h['cpu_percent']}%", cell_style),
                Paragraph(f"{h['ram_percent']}%", cell_style),
                Paragraph(f"{h['disk_percent']}%", cell_style),
                Paragraph(h["network_status"], cell_style),
                Paragraph(h["overall_status"], cell_style)
            ])
        hist_table = Table(hist_table_data, colWidths=[120, 75, 75, 75, 95, 100])
        hist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(hist_table)
    else:
        story.append(Paragraph("<i>No historical metrics recorded yet.</i>", cell_style))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#cbd5e1'), spaceBefore=5, spaceAfter=8))
    
    footer_text = "Generated by AI-Powered System Monitoring Platform &bull; Academic MCA Project Report &bull; Confidential Internal Audit Document"
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7, leading=9, textColor=colors.HexColor('#64748b'), alignment=1)
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

if __name__ == '__main__':
    print("=" * 60)
    print("  PDF REPORT GENERATOR MODULE SELF-TEST")
    print("=" * 60)
    pdf_buf = generate_pdf_report()
    pdf_bytes = pdf_buf.getvalue()
    print(f"  PDF Generated Successfully: {len(pdf_bytes)} bytes")
    print(f"  Header Signature          : {pdf_bytes[:4].decode('latin-1')}")
    print("=" * 60)
    print("PDF report generator self-test completed successfully!")
