#!/usr/bin/env python3
import sqlite3
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import smtplib
from email.message import EmailMessage

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

USER_HOME = Path.home()
DEFAULT_DB_PATH = USER_HOME / "local_grid" / "logs" / "grid_telemetry.db"
DEFAULT_PDF_PATH = USER_HOME / "local_grid" / "logs" / "grid_performance_report.pdf"

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Grid Reporter CLI: Search, filter, export, and email hardware telemetry reports."
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=20,
        help="Limit output to the last N tries (default: 20). Use 0 or -1 for all records."
    )
    parser.add_argument(
        "-d", "--date",
        type=str,
        default=None,
        help="Filter runs by date (YYYY-MM-DD format)."
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="Filter runs by specific model name match."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=str(DEFAULT_PDF_PATH),
        help="Custom file path for generated PDF report export."
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help="Custom SQLite telemetry database path."
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="Recipient email address to dispatch the compiled PDF report."
    )
    parser.add_argument(
        "--smtp-server",
        type=str,
        default="smtp.gmail.com",
        help="SMTP server hostname (default: smtp.gmail.com)."
    )
    parser.add_argument(
        "--smtp-port",
        type=int,
        default=587,
        help="SMTP port (default: 587)."
    )
    parser.add_argument(
        "--smtp-user",
        type=str,
        default=os.getenv("GRID_SMTP_USER"),
        help="Sender email username or environment variable GRID_SMTP_USER."
    )
    parser.add_argument(
        "--smtp-pass",
        type=str,
        default=os.getenv("GRID_SMTP_PASS"),
        help="Sender email app password or environment variable GRID_SMTP_PASS."
    )
    return parser.parse_args()

def query_database(db_path, date_filter=None, model_filter=None, limit=20):
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"[ERROR] Telemetry database not found at {db_file}. Run benchmarks first!")
        sys.exit(1)

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    query = "SELECT timestamp, model_name, target_tokens, actual_tokens, tokens_per_sec, wall_time_sec, load_ms, prefill_tps, decode_tps FROM hardware_runs WHERE 1=1"
    params = []

    if date_filter:
        query += " AND timestamp LIKE ?"
        params.append(f"{date_filter}%")
    if model_filter:
        query += " AND model_name LIKE ?"
        params.append(f"%{model_filter}%")

    query += " ORDER BY run_id DESC"
    if limit > 0:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def print_terminal_report(rows, limit):
    print("\n" + "=" * 90)
    print(f"📊 LOCAL GRID HARDWARE TELEMETRY REPORT (Showing up to {limit} records)")
    print("=" * 90)
    print(f"{'TIMESTAMP':<20} | {'MODEL NAME':<18} | {'TOKENS':<8} | {'DECODE TPS':<10} | {'PREFILL TPS':<11} | {'LOAD (MS)':<8}")
    print("-" * 90)
    
    if not rows:
        print("No telemetry records found matching the specified parameters.")
    else:
        for r in rows:
            ts, model, target, actual, tps, wall, load, prefill, decode = r
            print(f"{ts:<20} | {model:<18} | {actual}/{target:<5} | {decode:<10.1f} | {prefill:<11.1f} | {load:<8.1f}")
    print("=" * 90)

def generate_pdf_report(rows, pdf_path, limit):
    pdf_file = Path(pdf_path)
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(pdf_file), pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=15
    )

    limit_label = f"Last {limit} Runs" if limit > 0 else "All Historical Runs"
    story.append(Paragraph("🚀 Local Grid Hardware Telemetry Performance Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Scope: {limit_label} | Total Captured: {len(rows)}", subtitle_style))
    story.append(Spacer(1, 10))

    if not rows:
        story.append(Paragraph("No telemetry records found matching the specified filters.", styles["Normal"]))
    else:
        table_data = [["Timestamp", "Model", "Tokens", "Decode TPS", "Prefill TPS", "Load (ms)"]]
        for r in rows:
            ts, model, target, actual, tps, wall, load, prefill, decode = r
            table_data.append([ts, model, f"{actual}/{target}", f"{decode:.1f}", f"{prefill:.1f}", f"{load:.1f}"])

        t = Table(table_data, colWidths=[110, 110, 65, 75, 75, 65])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
        ]))
        story.append(t)

    doc.build(story)
    print(f"📄 PDF Report compiled successfully -> [{pdf_file}]")
    return str(pdf_file)

def send_email_report(pdf_path, recipient, smtp_server, smtp_port, user, password):
    if not user or not password:
        print("[ERROR] SMTP credentials missing. Set --smtp-user/--smtp-pass or environment variables GRID_SMTP_USER/GRID_SMTP_PASS.")
        return

    msg = EmailMessage()
    msg["Subject"] = f"📊 Local Grid Hardware Telemetry Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = user
    msg["To"] = recipient
    msg.set_content("Attached is your automated hardware telemetry and token throughput benchmark report generated by the Local Grid Agent.")

    with open(pdf_path, "rb") as f:
        file_data = f.read()
        file_name = Path(pdf_path).name

    msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        print(f"📧 Report successfully emailed to [{recipient}]!")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")

def main():
    args = parse_arguments()
    rows = query_database(args.db, date_filter=args.date, model_filter=args.model, limit=args.limit)
    
    # Print clean report to screen
    print_terminal_report(rows, args.limit)
    
    # Compile PDF report
    pdf_file = generate_pdf_report(rows, args.output, args.limit)

    if args.email:
        send_email_report(pdf_file, args.email, args.smtp_server, args.smtp_port, args.smtp_user, args.smtp_pass)

if __name__ == "__main__":
    main()
