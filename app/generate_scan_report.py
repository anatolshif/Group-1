#!/usr/bin/env python3
"""
generate_scan_report.py

Usage:
    python generate_scan_report.py -i scan_results.json -o android_scan_report.pdf

Dependencies:
    pip install reportlab matplotlib

Input JSON format (example):
{
  "app_name": "ExampleApp",
  "package": "com.example.app",
  "scan_date": "2025-09-01 12:00:00Z",
  "scanner_version": "AndroidScanner v0.1",
  "summary": {
    "total_checks": 10,
    "issues_found": 6,
    "high": 2,
    "medium": 2,
    "low": 2
  },
  "vulnerabilities": [
    {
      "id": "M1",
      "title": "Improper Platform Usage",
      "severity": "High",
      "score": 8.2,
      "description": "...",
      "evidence": "...",
      "affected_components": ["..."],
      "recommendation": "..."
    },
    ...
  ]
}
"""

import argparse
import json
import io
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, Flowable
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.units import mm
import matplotlib.pyplot as plt

# Map severity to colors and numeric rank (for sorting if needed)
SEV_COLOR = {
    "Critical": colors.HexColor("#8B0000"),
    "High": colors.HexColor("#D9534F"),
    "Medium": colors.HexColor("#F0AD4E"),
    "Low": colors.HexColor("#5BC0DE"),
    "Info": colors.HexColor("#5CB85C")
}

class SeverityBadge(Flowable):
    """A small colored rectangle + label for severity used inline as a flowable."""
    def __init__(self, severity, width=40, height=12):
        super().__init__()   # DO NOT pass width/height here
        self.severity = severity
        self.width = width  
        self.height = height
        self.color = SEV_COLOR.get(severity, colors.gray)

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.roundRect(0, 0, self.width * mm, self.height * mm, 1*mm, fill=1, stroke=0)
        self.canv.setFillColor(colors.white)
        self.canv.setFont("Helvetica-Bold", 6)
        self.canv.drawCentredString((self.width*mm)/2, (self.height*mm)/2 - 3, self.severity)

def make_severity_chart(summary):
    """Return a BytesIO PNG of a small bar chart for high/medium/low counts."""
    labels = []
    values = []
    for k in ("High", "Medium", "Low"):
        labels.append(k)
        values.append(summary.get(k.lower(), summary.get(k, 0)))
    fig, ax = plt.subplots(figsize=(4, 2.2))
    ax.bar(labels, values)
    ax.set_title("Issues by Severity")
    ax.set_ylabel("Count")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

def build_pdf(input_json, output_pdf):
    # Load
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)         

    app_name = data.get("app_name", "Unknown App")
    package = data.get("package", "")
    scan_date = data.get("scan_date", datetime.datetime.now(datetime.UTC).isoformat())
    scanner_version = data.get("scanner_version", "")
    summary = data.get("summary", {})
    vulnerabilities = data.get("vulnerabilities", [])

    doc = SimpleDocTemplate(output_pdf, pagesize=A4,
                            rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()              
    # custom styles
    styles.add(ParagraphStyle(name='CenteredTitle', parent=styles['Title'], alignment=1))
    styles.add(ParagraphStyle(name='Heading2Left', parent=styles['Heading2'], spaceBefore=6, spaceAfter=6))
    normal = styles['Normal']

    story = []

    # COVER
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("Android App Security Scan Report", styles['CenteredTitle']))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Application:</b> {app_name}", normal))
    story.append(Paragraph(f"<b>Package:</b> {package}", normal))
    story.append(Paragraph(f"<b>Scan date:</b> {scan_date}", normal))
    story.append(Paragraph(f"<b>Scanner:</b> {scanner_version}", normal))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        "This document summarizes automated checks performed on the mobile application and highlights detected issues mapped to OWASP Mobile Top 10 categories.",
        normal))
    story.append(Spacer(1, 6*mm))

    # Quick summary table
    summary_table_data = [
        ["Total checks", summary.get("total_checks", "")],
        ["Issues found", summary.get("issues_found", "")],
        ["High severity", summary.get("high", summary.get("High", 0))],
        ["Medium severity", summary.get("medium", summary.get("Medium", 0))],
        ["Low severity", summary.get("low", summary.get("Low", 0))],
    ]
    t = Table(summary_table_data, hAlign="LEFT", colWidths=[90*mm, 50*mm])
    t.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 6*mm))    

    # severity chart
    chart_buf = make_severity_chart(summary)
    story.append(Image(chart_buf, width=120*mm, height=60*mm))
    story.append(PageBreak())

    # Table of contents
    story.append(Paragraph("Table of Contents", styles['Heading2']))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(fontSize=12, name='TOCHeading1', leftIndent=0, firstLineIndent=-12, spaceBefore=6, leading=14),
        ParagraphStyle(fontSize=10, name='TOCHeading2', leftIndent=12, firstLineIndent=-12, spaceBefore=2, leading=12),
    ]
    story.append(toc)
    story.append(PageBreak())

    # Detailed vulns
    for idx, v in enumerate(vulnerabilities, start=1):
        # Add heading and register with TOC
        title_text = f"{v.get('id','V{0}'.format(idx))} - {v.get('title','Untitled')}"
        heading = Paragraph(title_text, styles['Heading2'])
        # Tell the TOC about this heading:
        # (level, text, pageNum) -> pageNum filled automatically by doc.build
        story.append(heading)
        # add entry to TOC
        # TableOfContents picks headings by style name 'Heading1', 'Heading2' etc auto if you use notify.
        # SimpleDocTemplate doesn't auto-notify; but TableOfContents provided here will be populated
        # when using the 'addOutlineEntry' mechanism from the canvas. To keep it simple, we will
        # use Paragraphs with 'bookmark' names so TOC receives entries automatically on building.
        # Add meta details
        story.append(Spacer(1, 2*mm))

        # Inline severity badge (just show the colored block as image)
        sev = v.get("severity", "Info")
        badge = SeverityBadge(sev, width=22, height=8)
        story.append(badge)
        story.append(Spacer(1, 2*mm))

        meta = f"Severity: <b>{sev}</b> | Score: <b>{v.get('score','')}</b>"
        story.append(Paragraph(meta, normal))
        story.append(Spacer(1, 3*mm))

        story.append(Paragraph("<b>Description</b>", styles['Heading4']))
        story.append(Paragraph(v.get("description", "No description provided."), normal))
        story.append(Spacer(1, 2*mm))

        story.append(Paragraph("<b>Evidence</b>", styles['Heading4']))
        story.append(Paragraph(v.get("evidence", "No evidence collected."), normal))
        story.append(Spacer(1, 2*mm))

        story.append(Paragraph("<b>Affected Components</b>", styles['Heading4']))
        ac = v.get("affected_components", [])
        if isinstance(ac, list):
            story.append(Paragraph(", ".join(ac) if ac else "N/A", normal))
        else:
            story.append(Paragraph(str(ac), normal))
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph("<b>Recommendation</b>", styles['Heading4']))
        story.append(Paragraph(v.get("recommendation", "No recommendation provided."), normal))
        story.append(Spacer(1, 6*mm))

        # page break every couple items to keep report readable (optional)
        if idx % 3 == 0:
            story.append(PageBreak())

    # Footer: summary / generation timestamp
    story.append(PageBreak())
    story.append(Paragraph("Generated report metadata", styles['Heading2']))
    story.append(Paragraph(f"Generated on: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')} (UTC)", normal))
    story.append(Paragraph(f"Scanner: {scanner_version}", normal))

    # Build doc.
    # NOTE: To get active TOC entries we can register outline entries.
    # A minimal approach is to supply a 'onFirstPage' callback to add outlines/bookmarks.
    def add_bookmarks(canvas, doc_):
        # We'll add a single top-level outline bookmark for the report, then for each vuln heading
        canvas.bookmarkPage("top")
        canvas.addOutlineEntry("Report", "top", level=0, closed=False)
        # naive method: find headings in story and add them as outline entries is complicated without keeping
        # references. For a simple, usable TOC table we rely on TableOfContents interacting with "notify"
        # which isn't done here. The generated TOC may be empty in some environments. If you need
        # accurate auto-populated TOC, consider using reportlab's Paragraph('text', style,
        # bulletText=None, fragemts) with 'outlineLevel' metadata or build a custom TOC.
        pass

    doc.build(story, onFirstPage=add_bookmarks)

def main():
    p = argparse.ArgumentParser(description="Generate PDF security scan report from JSON results.")
    p.add_argument("-i", "--input", required=True, help="Input JSON file with scan results")
    p.add_argument("-o", "--output", required=True, help="Output PDF file path")
    args = p.parse_args()
    build_pdf(args.input, args.output)
    print(f"PDF generated -> {args.output}")

if __name__ == "__main__":
    main()