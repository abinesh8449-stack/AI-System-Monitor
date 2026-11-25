import os
import sys
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).resolve().parent
SCREENSHOTS_DIR = BASE_DIR / "static" / "img" / "screenshots"
OUTPUT_PDF = BASE_DIR / "AI_System_Monitor_Project_Documentation.pdf"

class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically for running header and footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Suppress running header/footer on title cover page
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header
        self.drawString(36, 756, "AI-Powered System Monitoring Platform — Technical Documentation")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 750, 576, 750)

        # Running Footer
        self.line(36, 42, 576, 42)
        self.drawString(36, 30, f"Generated: {datetime.now().strftime('%Y-%m-%d')} | Confidential Academic Dossier")
        self.drawRightString(576, 30, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#2563eb'),
        alignment=1,
        spaceAfter=20
    )

    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155'),
        leftIndent=14,
        spaceAfter=3
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    caption_style = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceBefore=4,
        spaceAfter=12
    )

    story = []

    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 40))
    story.append(Paragraph("AI-POWERED SYSTEM MONITORING PLATFORM", title_style))
    story.append(Paragraph("Comprehensive Project Documentation & Technical Architecture Dossier", subtitle_style))
    story.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor('#2563eb'), spaceBefore=10, spaceAfter=25, hAlign='CENTER'))

    cover_info = [
        [Paragraph("<b>Project Title:</b>", table_cell), Paragraph("AI-Powered System Monitoring & Autonomous Self-Healing Platform", table_cell)],
        [Paragraph("<b>Technology Stack:</b>", table_cell), Paragraph("Python 3.11, Flask, psutil, SQLite (WAL), Chart.js, ReportLab", table_cell)],
        [Paragraph("<b>Domain / Category:</b>", table_cell), Paragraph("AIOps / Real-Time Systems Observability / Automated Incident Remediation", table_cell)],
        [Paragraph("<b>Academic Scope:</b>", table_cell), Paragraph("Final Year Academic Project / MCA / Computer Science & Engineering", table_cell)],
        [Paragraph("<b>Publication Date:</b>", table_cell), Paragraph(datetime.now().strftime("%B %d, %Y"), table_cell)],
        [Paragraph("<b>Host Architecture:</b>", table_cell), Paragraph("Cross-Platform (Windows, Linux, macOS) — Production-Style Full Stack", table_cell)],
    ]
    cover_table = Table(cover_info, colWidths=[130, 370])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 40))
    story.append(Paragraph("<b>Abstract</b>", h2_style))
    abstract_text = (
        "Modern computing infrastructures require continuous, real-time observability to prevent resource starvation, "
        "silent performance bottlenecks, and unplanned downtime. Traditional system monitors passively display raw hardware "
        "numbers without providing root-cause diagnostic context or remediation mechanisms. This project delivers an "
        "end-to-end, full-stack <b>AI-Powered System Monitoring Platform</b> that continuously ingests hardware telemetry "
        "(CPU, RAM, Disk, Network I/O, process hierarchy) via <code>psutil</code>, evaluates system condition against configurable "
        "thresholds into <b>HEALTHY</b>, <b>WARNING</b>, or <b>CRITICAL</b> operational tiers, and runs a modular "
        "<b>AI Diagnostic & Root-Cause Recommendation Engine</b>. When critical anomalies arise, the platform attributes the "
        "bottleneck to specific process IDs (PIDs) and enables <b>Autonomous AI Self-Healing</b> (process termination, OS working-set "
        "RAM reclamation, and cache purges). Complete with rate-limited SMTP incident/recovery alerts, searchable historical "
        "audit logs, and one-click PDF/CSV report generation, the platform provides a complete enterprise-grade observability solution."
    )
    story.append(Paragraph(abstract_text, body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Keywords:</b> AIOps, System Monitoring, Autonomous Self-Healing, psutil, Flask, Real-Time Telemetry, Root-Cause Analysis, Chart.js, SQLite WAL.", meta_style))

    story.append(PageBreak())

    # ==================== 1. SYSTEM ARCHITECTURE ====================
    story.append(Paragraph("1. System Architecture & Modular Pipeline", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=10))

    arch_text = (
        "The application is engineered with a modular, decoupled architecture consisting of five distinct operational tiers. "
        "Kernel telemetry sampling is completely decoupled from UI rendering and database writes, ensuring zero page-load latency "
        "and preventing redundant database bloat."
    )
    story.append(Paragraph(arch_text, body_style))

    modules_data = [
        [Paragraph("<b>Component Layer</b>", table_header), Paragraph("<b>Key Modules</b>", table_header), Paragraph("<b>Responsibilities & Implementation</b>", table_header)],
        [
            Paragraph("<b>Telemetry Collection</b>", table_cell),
            Paragraph("<code>system_monitor.py</code><br/><code>network_monitor.py</code>", table_cell),
            Paragraph("Extracts core-level CPU %, clock frequencies, physical/virtual RAM buffers, mount partition capacities, bandwidth transfer rates (KB/s), socket reachability, and top consuming process PIDs via <code>psutil</code>.", table_cell)
        ],
        [
            Paragraph("<b>Health Evaluation</b>", table_cell),
            Paragraph("<code>health_checker.py</code>", table_cell),
            Paragraph("Applies configurable thresholds from <code>config.py</code>. Categorizes individual resources and derives overall state via a prioritized health matrix (HEALTHY, WARNING, CRITICAL).", table_cell)
        ],
        [
            Paragraph("<b>AI Diagnosis & Remediation</b>", table_cell),
            Paragraph("<code>recommendation_engine.py</code><br/><code>remediation_engine.py</code>", table_cell),
            Paragraph("Correlates single and multi-resource anomalies (e.g., simultaneous CPU+RAM spikes). Pinpoints offending processes, issues structured remediation steps, and executes self-healing (PID kill, RAM working-set trim, cache wipe).", table_cell)
        ],
        [
            Paragraph("<b>Persistence & Audit</b>", table_cell),
            Paragraph("<code>database.py</code><br/><code>monitoring.db</code>", table_cell),
            Paragraph("Stores periodic snapshots, incident alerts, recovery events, and user accounts in SQLite using Write-Ahead Logging (WAL) for high-concurrency read/write operations.", table_cell)
        ],
        [
            Paragraph("<b>Alerts & Reporting</b>", table_cell),
            Paragraph("<code>email_alert.py</code><br/><code>pdf_report.py</code><br/><code>csv_report.py</code>", table_cell),
            Paragraph("Dispatches SMTP incident emails with anti-spam cooldown gating and automated recovery notices. Compiles vector PDF reports (ReportLab) and raw CSV datasets on demand.", table_cell)
        ],
        [
            Paragraph("<b>Web Presentation</b>", table_cell),
            Paragraph("<code>app.py</code><br/><code>dashboard.js</code><br/><code>charts.js</code>", table_cell),
            Paragraph("Bootstrap 5 dark cyber-themed dashboard with animated Chart.js streaming buffers (15-point rolling window) polled asynchronously via Fetch API every 1.5 seconds.", table_cell)
        ],
    ]
    mod_table = Table(modules_data, colWidths=[100, 110, 290])
    mod_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(mod_table)

    story.append(PageBreak())

    # ==================== 2. SCREENSHOTS & INTERFACE WALKTHROUGH ====================
    story.append(Paragraph("2. Application Visual Tour & Screen Interfaces", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=10))

    def add_screen_section(title, desc_list, img_filename, width=490, height=270):
        story.append(Paragraph(title, h2_style))
        for d in desc_list:
            story.append(Paragraph(f"&bull; {d}", bullet_style))
        img_path = SCREENSHOTS_DIR / img_filename
        if img_path.exists():
            story.append(Spacer(1, 4))
            story.append(Image(str(img_path), width=width, height=height, hAlign='CENTER'))
            story.append(Paragraph(f"Figure: {title}", caption_style))
        else:
            story.append(Paragraph(f"<i>[Image {img_filename} not found]</i>", caption_style))
        story.append(Spacer(1, 6))

    # Screen 1: Login
    add_screen_section(
        "2.1 Authentication Portal (System Console Login)",
        [
            "Session-based access control with SHA-256 and Scrypt cryptographic password hashing.",
            "Session cookies secured with HttpOnly and SameSite=Lax flags to mitigate XSS and CSRF.",
            "Visual error flash alerts upon invalid credentials and automatic session expiration handling."
        ],
        "01_login_page.png",
        width=480, height=270
    )

    story.append(PageBreak())

    # Screen 2: Dashboard Overview
    add_screen_section(
        "2.2 Real-Time Observability Command Center (Nominal State)",
        [
            "Prominent Overall System Health status card displaying real-time operational tier (HEALTHY).",
            "Individual metric gauges for CPU (cores, frequency), RAM (used/total), Storage, and Network I/O.",
            "Live AI Diagnostic & Root-Cause card detailing detected condition, cause, immediate action, and preventive plan.",
            "Active AI Remediation action bar with Execute AI Self-Healing, Flush RAM & Cache, and Incident Simulators."
        ],
        "02_dashboard_overview.png",
        width=500, height=290
    )

    story.append(PageBreak())

    # Screen 3: Critical Anomaly
    add_screen_section(
        "2.3 Autonomous AI Anomaly Detection & Critical Root-Cause Attribution",
        [
            "Dynamic status transition to SYSTEM CRITICAL (red) when resources cross configured thresholds.",
            "Correlates hardware telemetry to isolate offending process (e.g., 'runaway_worker_sim.exe' PID 99412 at 79.3% CPU).",
            "AI Action bar illuminates red (CRITICAL: Execute AI Self-Healing Now), enabling instant operator resolution.",
            "Automatically updates without full-page reloads using asynchronous JavaScript polling."
        ],
        "07_ai_critical_incident.png",
        width=500, height=295
    )

    story.append(PageBreak())

    # Screen 4: Extended Dashboard (Charts & Process Isolation)
    add_screen_section(
        "2.4 Live Rolling Charts & Targeted Process Termination",
        [
            "Four synchronized Chart.js streams: CPU utilization, Memory utilization, Storage capacity, and Network throughput (KB/s).",
            "Top Processes tables ranked by instantaneous CPU and RAM utilization.",
            "Targeted Kill button terminates runaway workloads, removes the row instantly from the DOM, and quarantines the PID."
        ],
        "02b_dashboard_full_view.png",
        width=440, height=520
    )

    story.append(PageBreak())

    # Screen 5: Telemetry History
    add_screen_section(
        "2.5 Historical System Telemetry Audit Directory (/history)",
        [
            "Tabular audit log of periodic telemetry snapshots persisted every 5 seconds by the background daemon.",
            "Multi-field search filter supporting keyword search, status filtering (ALL, HEALTHY, WARNING, CRITICAL), and date ranges.",
            "Server-side pagination with record count tracking and quick-export shortcuts to CSV and PDF."
        ],
        "03_monitoring_history.png",
        width=500, height=290
    )

    story.append(PageBreak())

    # Screen 6: Alerts Management
    add_screen_section(
        "2.6 Incident Alert Management & Automated Recovery Directory (/alerts)",
        [
            "Logs every threshold breach with timestamp, affected resource, trigger value, severity rating, and AI recommendation.",
            "Anti-spam alert cooldown gating (300 seconds default) prevents mailbox saturation during sustained spikes.",
            "Automated recovery detection: marks previous incidents as Recovered and logs recovery timestamps when metrics normalize."
        ],
        "04_alerts_management.png",
        width=500, height=290
    )

    story.append(PageBreak())

    # Screen 7: Server Information
    add_screen_section(
        "2.7 Hardware & Operating System Topography (/server-info)",
        [
            "Deep hardware inspection: Host machine name, OS distribution, kernel release version, architecture, and uptime.",
            "Processor & Memory hierarchy: Physical core count, logical thread count, base clock frequency, and RAM capacity.",
            "Mounted storage partition inspection: File system types, mount points, volume capacities, and free disk space.",
            "Network adapter configuration: IPv4 addresses, subnet masks, MAC addresses, link speeds, and connection states."
        ],
        "05_server_info.png",
        width=500, height=290
    )

    story.append(PageBreak())

    # Screen 8: Reports Center
    add_screen_section(
        "2.8 Executive Audit Report Generation Center (/reports)",
        [
            "One-click generation and streaming of publication-grade ReportLab PDF audit reports.",
            "Direct download of raw CSV telemetry datasets for analysis in spreadsheet applications or data science pipelines.",
            "Executive summary cards showing retained snapshot counts, historical average CPU/RAM, and total incident counts."
        ],
        "06_audit_reports.png",
        width=500, height=290
    )

    story.append(PageBreak())

    # ==================== 3. DATABASE SCHEMA & API SPECIFICATION ====================
    story.append(Paragraph("3. Database Schema & REST API Specifications", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=10))

    story.append(Paragraph("3.1 SQLite WAL Database Architecture", h2_style))
    db_desc = (
        "The application utilizes SQLite configured in Write-Ahead Logging (WAL) mode (<code>PRAGMA journal_mode=WAL</code>). "
        "WAL mode allows background threads to write telemetry snapshots without blocking concurrent dashboard read queries. "
        "The schema uses standard ANSI SQL types, primary keys, and foreign keys, allowing seamless migration to PostgreSQL."
    )
    story.append(Paragraph(db_desc, body_style))

    schema_data = [
        [Paragraph("<b>Table Name</b>", table_header), Paragraph("<b>Key Columns</b>", table_header), Paragraph("<b>Description & Constraints</b>", table_header)],
        [
            Paragraph("<b>users</b>", table_cell),
            Paragraph("<code>id, username, password_hash, created_at</code>", table_cell),
            Paragraph("Stores authenticated operator credentials with salted cryptographic hashes. Unique constraint on <code>username</code>.", table_cell)
        ],
        [
            Paragraph("<b>monitoring_history</b>", table_cell),
            Paragraph("<code>id, timestamp, cpu_percent, ram_percent, disk_percent, network_status, network_upload_speed, network_download_speed, overall_status, ai_recommendation, is_alert_triggered</code>", table_cell),
            Paragraph("Periodic snapshots captured every 5 seconds. Stores raw metrics, derived health status, AI diagnostic text, and alert dispatch flags.", table_cell)
        ],
        [
            Paragraph("<b>alerts</b>", table_cell),
            Paragraph("<code>id, timestamp, resource, value, severity, problem, recommendation, email_status, is_recovered, recovered_at</code>", table_cell),
            Paragraph("Incident lifecycle table tracking threshold crossings, severity levels, SMTP dispatch status, and automated recovery timestamps.", table_cell)
        ],
        [
            Paragraph("<b>recommendations</b>", table_cell),
            Paragraph("<code>id, timestamp, problem, severity, cause, action, prevention</code>", table_cell),
            Paragraph("Audit trail of generated AI recommendations, updated only when system conditions transition between states.", table_cell)
        ],
    ]
    schema_table = Table(schema_data, colWidths=[110, 160, 230])
    schema_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(schema_table)

    story.append(Spacer(1, 14))
    story.append(Paragraph("3.2 Protected REST API Reference", h2_style))

    api_data = [
        [Paragraph("<b>HTTP Method</b>", table_header), Paragraph("<b>Endpoint Route</b>", table_header), Paragraph("<b>Parameters / Body</b>", table_header), Paragraph("<b>Description</b>", table_header)],
        [Paragraph("<code>GET</code>", table_cell), Paragraph("<code>/api/metrics</code>", table_cell), Paragraph("None", table_cell), Paragraph("Instantaneous telemetry stream polled by dashboard every 1.5s.", table_cell)],
        [Paragraph("<code>GET</code>", table_cell), Paragraph("<code>/api/health</code>", table_cell), Paragraph("None", table_cell), Paragraph("Centralized health classification breakdown (HEALTHY, WARNING, CRITICAL).", table_cell)],
        [Paragraph("<code>GET</code>", table_cell), Paragraph("<code>/api/summary</code>", table_cell), Paragraph("None", table_cell), Paragraph("Aggregate metric counters, active alert tallies, and uptime.", table_cell)],
        [Paragraph("<code>POST</code>", table_cell), Paragraph("<code>/api/remediate/execute</code>", table_cell), Paragraph("<code>action_type, pid</code>", table_cell), Paragraph("Executes AI remediation (auto_heal, clean_cache, or targeted process kill).", table_cell)],
        [Paragraph("<code>POST</code>", table_cell), Paragraph("<code>/api/remediate/simulate</code>", table_cell), Paragraph("<code>type: cpu|ram|multi|stop</code>", table_cell), Paragraph("Triggers or clears controlled critical incident simulations.", table_cell)],
        [Paragraph("<code>POST</code>", table_cell), Paragraph("<code>/api/remediate/toggle-auto</code>", table_cell), Paragraph("<code>enabled: boolean</code>", table_cell), Paragraph("Toggles autonomous background AI self-healing policy.", table_cell)],
        [Paragraph("<code>GET</code>", table_cell), Paragraph("<code>/reports/download/pdf</code>", table_cell), Paragraph("None", table_cell), Paragraph("Streams vector ReportLab executive PDF health audit report.", table_cell)],
        [Paragraph("<code>GET</code>", table_cell), Paragraph("<code>/reports/download/csv</code>", table_cell), Paragraph("None", table_cell), Paragraph("Streams raw tabular CSV telemetry dataset.", table_cell)],
    ]
    api_table = Table(api_data, colWidths=[65, 125, 120, 190])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(api_table)

    story.append(PageBreak())

    # ==================== 4. VIVA VOCE & ACADEMIC Q&A ====================
    story.append(Paragraph("4. Academic Viva Voce & Demonstration Q&A", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2563eb'), spaceBefore=2, spaceAfter=10))

    viva_qa = [
        ("Q1: What is the primary objective of this project?",
         "To develop an intelligent, full-stack system monitoring platform that continuously monitors host hardware metrics in real time, classifies health condition (HEALTHY, WARNING, CRITICAL), and employs an AI recommendation engine with autonomous self-healing to resolve critical performance bottlenecks."),

        ("Q2: Why use psutil instead of shell commands like top or tasklist?",
         "psutil directly invokes low-level C syscalls, kernel structures, and OS APIs without spawning sub-shell processes. This makes it cross-platform (Windows, Linux, macOS), highly performant, thread-safe, and free from shell injection vulnerabilities."),

        ("Q3: How is real-time visualization achieved without database or browser overload?",
         "We decoupled UI polling from database writes. The frontend polls /api/metrics every 1.5 seconds and updates in-memory rolling Chart.js buffers (15 data points maximum). Meanwhile, a separate background daemon writes snapshots to SQLite every 5 seconds, avoiding database bloat."),

        ("Q4: How does the AI Recommendation Engine perform multi-resource correlation?",
         "It correlates cross-resource patterns rather than evaluating isolated thresholds. For instance, a simultaneous CPU and RAM spike indicates a runaway batch worker or memory leak. The engine attributes the incident directly to offending process PIDs and outputs structured guidance: Problem, Severity, Possible Cause, Immediate Action, and Prevention."),

        ("Q5: How does the Active AI Self-Healing mechanism resolve critical bottlenecks?",
         "The remediation engine provides both autonomous and manual recovery workflows: terminating runaway workloads, running garbage collection (gc.collect()), triggering OS working-set memory reclamation (SetProcessWorkingSetSize on Windows), and clearing stale temporary cache files."),

        ("Q6: How does the Alert Cooldown mechanism prevent email flooding?",
         "The alert manager enforces a configurable cooldown window (default: 300 seconds). When a critical state is breached, an alert email is sent and a cooldown timer starts. Subsequent critical samples within the window are recorded locally but suppressed from email re-dispatch."),

        ("Q7: How does Automated Recovery Detection function?",
         "When a system previously in a CRITICAL or WARNING state normalizes back to HEALTHY, the engine detects this positive state transition, marks open alert records in SQLite with is_recovered = 1 and a recovery timestamp, and logs a recovery audit event."),

        ("Q8: How does the PDF reporting engine generate documents?",
         "Using ReportLab. It builds vector-grade PDF documents programmatically with flowable tables, paragraphs, custom typography, and page headers/footers without requiring headless browser binaries or external rendering dependencies."),

        ("Q9: How are operator credentials secured?",
         "Passwords are never stored in plain text. They are hashed using modern cryptographic algorithms (Scrypt via Werkzeug) with unique random salts. Authentication is checked using constant-time hash comparisons to prevent timing attacks."),

        ("Q10: What test coverage is implemented?",
         "A comprehensive test suite of 30 automated unit and integration tests covering telemetry collection, health evaluation boundaries, AI recommendation correlation, process isolation, authentication guards, and binary report streaming.")
    ]

    for q, a in viva_qa:
        story.append(Paragraph(f"<b>{q}</b>", h3_style))
        story.append(Paragraph(a, body_style))
        story.append(Spacer(1, 4))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Project documentation PDF generated successfully at: {OUTPUT_PDF}")
    return OUTPUT_PDF

if __name__ == "__main__":
    build_pdf()
