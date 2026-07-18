from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_pdf_report(data: dict) -> BytesIO:
    """Compiles the calculated metrics and suggestions into a structured, printable ReportLab PDF stream."""
    buffer = BytesIO()
    # Margins: 36pt = 0.5 inch
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Styles for premium presentation
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#4f46e5"),
        spaceAfter=12,
    )

    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    bold_body = ParagraphStyle("BoldBody", parent=body_style, fontName="Helvetica-Bold")

    story = []

    # 1. Document Title
    story.append(Paragraph("ATS Optimization Analysis Report", title_style))
    story.append(
        Paragraph(f"Method of Parsing: {data.get('extraction_method', 'N/A')}", body_style)
    )
    story.append(Spacer(1, 10))

    # 2. Main Metrics Table
    metrics = data.get("metrics", {})
    score_data = [
        [
            Paragraph("<b>Overall Score</b>", body_style),
            Paragraph("<b>Skill Match</b>", body_style),
            Paragraph("<b>Semantic Match</b>", body_style),
            Paragraph("<b>Resume Strength</b>", body_style),
        ],
        [
            Paragraph(
                f"<font color='#4f46e5'><b>{metrics.get('final_score', 0):.2f}%</b></font>",
                ParagraphStyle("ScoreMain", parent=title_style, fontSize=18),
            ),
            Paragraph(
                f"<b>{metrics.get('skill_match', 0):.2f}%</b>",
                ParagraphStyle(
                    "ScoreSkl",
                    parent=title_style,
                    fontSize=18,
                    textColor=colors.HexColor("#0f172a"),
                ),
            ),
            Paragraph(
                f"<b>{metrics.get('semantic_match', 0):.2f}%</b>",
                ParagraphStyle(
                    "ScoreSem",
                    parent=title_style,
                    fontSize=18,
                    textColor=colors.HexColor("#0f172a"),
                ),
            ),
            Paragraph(
                f"<b>{metrics.get('resume_strength', 0):.2f}%</b><br/><font size='7'>{metrics.get('badge', '')}</font>",
                body_style,
            ),
        ],
    ]
    t = Table(score_data, colWidths=[135, 135, 135, 135])
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 12))

    # 3. Dynamic Resume Verdict
    story.append(Paragraph("Resume Verdict", section_style))
    story.append(Paragraph(data.get("verdict", ""), body_style))
    story.append(Spacer(1, 10))

    # 4. ATS Checklist
    story.append(Paragraph("ATS Structural Checklist", section_style))
    chk = data.get("checklist", {})

    items = [
        ("Contact Information", chk.get("contact_info")),
        ("Skills Section", chk.get("skills")),
        ("Projects Section", chk.get("projects")),
        ("Education Section", chk.get("education")),
        ("Work Experience", chk.get("experience")),
        ("Certifications", chk.get("certifications")),
        ("LinkedIn Profile", chk.get("linkedin")),
        ("GitHub Profile", chk.get("github")),
    ]

    chk_rows = []
    for i in range(0, len(items), 2):
        item1_name, item1_val = items[i]
        item2_name, item2_val = items[i + 1]

        status1 = (
            "<font color='green'><b>PASS</b></font>"
            if item1_val
            else "<font color='red'><b>FAIL</b></font>"
        )
        status2 = (
            "<font color='green'><b>PASS</b></font>"
            if item2_val
            else "<font color='red'><b>FAIL</b></font>"
        )

        chk_rows.append(
            [
                Paragraph(item1_name, body_style),
                Paragraph(status1, body_style),
                Paragraph(item2_name, body_style),
                Paragraph(status2, body_style),
            ]
        )

    t_chk = Table(chk_rows, colWidths=[180, 90, 180, 90])
    t_chk.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_chk)
    story.append(Spacer(1, 12))

    # 5. Missing Skills Roadmap
    story.append(Paragraph("Prioritized Missing Skills & Learning Roadmap", section_style))
    missing_skills = data.get("skills", {}).get("missing", {})

    flat_missing = []
    for cat, s_list in missing_skills.items():
        for s in s_list:
            flat_missing.append(s)

    if not flat_missing:
        story.append(Paragraph("No missing skills! Excellent keyword compliance.", body_style))
    else:
        for idx, s in enumerate(flat_missing[:8]):  # Top 8 missing skills in PDF
            story.append(
                Paragraph(
                    f"<b>Priority {idx+1}: {s['name']}</b> (Difficulty: {s['difficulty']} | Est. Time: {s.get('est_time', '7 Days')})",
                    bold_body,
                )
            )
            story.append(Spacer(1, 3))

    story.append(Spacer(1, 10))

    # 6. Prioritized Improvement Suggestions
    story.append(Paragraph("Prioritized Improvement Suggestions", section_style))
    suggestions = data.get("suggestions", [])
    for idx, sugg in enumerate(suggestions[:6]):  # top 6 suggestions
        story.append(
            Paragraph(
                f"<b>[{sugg.get('priority')} Priority] - {sugg.get('title')}</b>: {sugg.get('description')}",
                body_style,
            )
        )
        story.append(Spacer(1, 3))

    doc.build(story)
    buffer.seek(0)
    return buffer
