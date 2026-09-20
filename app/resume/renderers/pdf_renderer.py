"""PDF renderer (reportlab).

Mirrors the DOCX layout closely. Both renderers honour the same template
config so generated DOCX and PDF look consistent.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.models.profile import Profile
from app.models.resume import TailoredResume
from app.resume.template_config import TemplateConfig, load_template


def render_pdf(
    resume: TailoredResume,
    profile: Profile,
    output_path: Path,
    *,
    template: str | None = None,
) -> Path:
    cfg: TemplateConfig = load_template(template or resume.template)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    base = getSampleStyleSheet()
    name_style = ParagraphStyle("Name", parent=base["Title"], fontSize=20, alignment=TA_CENTER)
    contact_style = ParagraphStyle(
        "Contact", parent=base["Normal"], alignment=TA_CENTER, fontSize=10
    )
    headline_style = ParagraphStyle(
        "Headline",
        parent=base["Italic"],
        alignment=TA_CENTER,
        fontSize=11,
    )
    h2 = ParagraphStyle("H2", parent=base["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)
    body = base["BodyText"]
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=14, bulletIndent=4, spaceAfter=2)
    italic_style = ParagraphStyle("Italic", parent=body, fontName="Helvetica-Oblique")

    flow: list[object] = []

    flow.append(Paragraph(profile.personal.full_name, name_style))
    contact_bits: list[str] = [profile.personal.email, profile.personal.phone]
    if profile.links.linkedin:
        contact_bits.append(str(profile.links.linkedin))
    if profile.links.github:
        contact_bits.append(str(profile.links.github))
    flow.append(Paragraph(" | ".join(contact_bits), contact_style))
    if resume.headline:
        flow.append(Paragraph(resume.headline, headline_style))
    flow.append(Spacer(1, 6))

    section_renderers = {
        "summary": lambda: _render_summary(flow, resume, h2, body),
        "skills": lambda: _render_skills(flow, resume, h2, body),
        "experience": lambda: _render_experience(flow, resume, cfg, h2, body, bullet, italic_style),
        "projects": lambda: _render_projects(flow, resume, cfg, h2, body, bullet, italic_style),
        "education": lambda: _render_education(flow, resume, h2, body, italic_style),
    }

    for section_name in cfg["section_order"]:
        renderer = section_renderers.get(section_name)
        if renderer is not None:
            renderer()

    doc.build(flow)
    return output_path


def _render_summary(
    flow: list[object], resume: TailoredResume, h2: ParagraphStyle, body: ParagraphStyle
) -> None:
    flow.append(Paragraph("SUMMARY", h2))
    flow.append(Paragraph(resume.summary, body))


def _render_skills(
    flow: list[object], resume: TailoredResume, h2: ParagraphStyle, body: ParagraphStyle
) -> None:
    if not resume.skills:
        return
    flow.append(Paragraph("SKILLS", h2))
    flow.append(Paragraph(", ".join(resume.skills), body))


def _render_experience(
    flow: list[object],
    resume: TailoredResume,
    cfg: TemplateConfig,
    h2: ParagraphStyle,
    body: ParagraphStyle,
    bullet: ParagraphStyle,
    italic: ParagraphStyle,
) -> None:
    if not resume.employment:
        return
    flow.append(Paragraph("EXPERIENCE", h2))
    for emp in resume.employment:
        flow.append(Paragraph(f"<b>{emp.title}</b> — {emp.company}", body))
        sub = f"{emp.location or ''} | {emp.start} – {emp.end or 'Present'}"
        flow.append(Paragraph(sub.strip(" |"), italic))
        if emp.bullets:
            flow.append(
                ListFlowable(
                    [
                        ListItem(Paragraph(b, bullet))
                        for b in emp.bullets[: cfg["max_bullets_per_role"]]
                    ],
                    bulletType="bullet",
                )
            )
        if cfg["include_tech_line"] and emp.tech:
            flow.append(Paragraph("Tech: " + ", ".join(emp.tech), italic))
        flow.append(Spacer(1, 4))


def _render_projects(
    flow: list[object],
    resume: TailoredResume,
    cfg: TemplateConfig,
    h2: ParagraphStyle,
    body: ParagraphStyle,
    bullet: ParagraphStyle,
    italic: ParagraphStyle,
) -> None:
    if not resume.projects:
        return
    flow.append(Paragraph("PROJECTS", h2))
    for proj in resume.projects:
        flow.append(Paragraph(f"<b>{proj.name}</b>", body))
        flow.append(Paragraph(proj.description, body))
        if proj.bullets:
            flow.append(
                ListFlowable(
                    [
                        ListItem(Paragraph(b, bullet))
                        for b in proj.bullets[: cfg["max_bullets_per_role"]]
                    ],
                    bulletType="bullet",
                )
            )
        if cfg["include_tech_line"] and proj.tech:
            flow.append(Paragraph("Tech: " + ", ".join(proj.tech), italic))
        flow.append(Spacer(1, 4))


def _render_education(
    flow: list[object],
    resume: TailoredResume,
    h2: ParagraphStyle,
    body: ParagraphStyle,
    italic: ParagraphStyle,
) -> None:
    if not resume.education:
        return
    flow.append(Paragraph("EDUCATION", h2))
    for edu in resume.education:
        flow.append(Paragraph(f"<b>{edu.degree}</b>, {edu.institution}", body))
        years = ""
        if edu.start_year and edu.end_year:
            years = f"{edu.start_year} – {edu.end_year}"
        elif edu.end_year:
            years = str(edu.end_year)
        if years:
            flow.append(Paragraph(years, italic))
