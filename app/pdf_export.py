from __future__ import annotations

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors

from .schemas import ResumeOut

def build_resume_pdf(resume: ResumeOut) -> bytes:
    # CJK-friendly built-in CID font
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        base_font = "STSong-Light"
    except Exception:
        base_font = "Helvetica"

    styles = getSampleStyleSheet()

    TitleCN = ParagraphStyle(
        name="TitleCN",
        parent=styles["Title"],
        fontName=base_font,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.black,
    )
    BodyCN = ParagraphStyle(
        name="BodyCN",
        parent=styles["BodyText"],
        fontName=base_font,
        fontSize=10.5,
        leading=14,
        alignment=TA_LEFT,
        textColor=colors.black,
    )
    H2CN = ParagraphStyle(
        name="H2CN",
        parent=styles["Heading2"],
        fontName=base_font,
        fontSize=12.5,
        leading=16,
        spaceBefore=8,
        spaceAfter=4,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=16*mm,
        bottomMargin=16*mm,
        title="Resume",
        author="Resume Builder",
    )

    story = []

    name = resume.contact.name or "Resume"
    story.append(Paragraph(name, TitleCN))

    contact_line_parts = [p for p in [resume.contact.email, resume.contact.phone, resume.contact.location, resume.contact.linkedin] if p]
    if contact_line_parts:
        story.append(Paragraph(" | ".join(contact_line_parts), BodyCN))
    if resume.headline:
        story.append(Paragraph(resume.headline, BodyCN))

    story.append(Spacer(1, 8))

    if resume.summary:
        story.append(Paragraph("Summary", H2CN))
        story.append(Paragraph(resume.summary, BodyCN))

    if resume.skills:
        story.append(Paragraph("Skills", H2CN))
        story.append(Paragraph("、".join(resume.skills), BodyCN))

    if resume.experience:
        story.append(Paragraph("Experience", H2CN))
        for exp in resume.experience:
            header = " — ".join([p for p in [exp.company, exp.role] if p])
            dates = " - ".join([p for p in [exp.start, exp.end] if p])
            meta = " | ".join([p for p in [exp.location, dates] if p])

            if header:
                story.append(Paragraph(f"<b>{header}</b>", BodyCN))
            if meta:
                story.append(Paragraph(meta, BodyCN))
            if exp.bullets:
                items = [ListItem(Paragraph(b, BodyCN), leftIndent=12) for b in exp.bullets]
                story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
            story.append(Spacer(1, 4))

    if resume.projects:
        story.append(Paragraph("Projects", H2CN))
        for pr in resume.projects:
            header = pr.name if pr.name else "Project"
            dates = " - ".join([p for p in [pr.start, pr.end] if p])
            meta = " | ".join([p for p in [pr.role, dates, pr.link] if p])

            story.append(Paragraph(f"<b>{header}</b>", BodyCN))
            if meta:
                story.append(Paragraph(meta, BodyCN))
            if pr.bullets:
                items = [ListItem(Paragraph(b, BodyCN), leftIndent=12) for b in pr.bullets]
                story.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
            story.append(Spacer(1, 4))

    if resume.education:
        story.append(Paragraph("Education", H2CN))
        for edu in resume.education:
            header = " — ".join([p for p in [edu.school, edu.degree, edu.major] if p])
            dates = " - ".join([p for p in [edu.start, edu.end] if p])

            if header:
                story.append(Paragraph(f"<b>{header}</b>", BodyCN))
            if dates:
                story.append(Paragraph(dates, BodyCN))
            story.append(Spacer(1, 3))

    if resume.certifications:
        story.append(Paragraph("Certifications", H2CN))
        for c in resume.certifications:
            story.append(Paragraph(f"• {c}", BodyCN))

    if resume.additional:
        story.append(Paragraph("Additional", H2CN))
        for a in resume.additional:
            story.append(Paragraph(f"• {a}", BodyCN))

    doc.build(story)
    return buf.getvalue()
