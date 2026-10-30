"""Composition PDF avec retour à la ligne et pagination automatiques (ReportLab)."""
from html import escape
from os import PathLike, fspath

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from generators.generate_sopra_docx import classify_competences, format_experiences, format_formations

PURPLE = colors.HexColor("#3E206D")
ORANGE = colors.HexColor("#FF5614")


def _text(value):
    if isinstance(value, list):
        return "\n".join(_text(item) for item in value)
    if isinstance(value, dict):
        return " — ".join(str(item) for item in value.values() if item)
    return str(value or "")


def generate_sopra_profile_pdf(cv_data, output_path):
    """Accepte un chemin ou un flux binaire ; ne tronque pas les listes ou missions."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("CVTitle", fontName="Helvetica-Bold", fontSize=23,
                              leading=28, textColor=PURPLE, spaceAfter=10))
    styles.add(ParagraphStyle("CVSection", fontName="Helvetica-Bold", fontSize=12,
                              leading=16, textColor=PURPLE, spaceBefore=14, spaceAfter=7,
                              keepWithNext=True))
    styles.add(ParagraphStyle("CVBody", fontName="Helvetica", fontSize=10,
                              leading=15, spaceAfter=5, splitLongWords=True))
    destination = fspath(output_path) if isinstance(output_path, PathLike) else output_path
    document = SimpleDocTemplate(destination, pagesize=A4, leftMargin=23*mm,
                                 rightMargin=23*mm, topMargin=24*mm, bottomMargin=22*mm,
                                 title="Curriculum vitae", author="")
    story = []

    def paragraph(value, style="CVBody"):
        text = _text(value)
        if text.strip():
            story.append(Paragraph(escape(text).replace("\n", "<br/>"), styles[style]))

    def section(title, value):
        if value:
            paragraph(title, "CVSection")
            # Une entrée peut occuper plusieurs lignes ou pages.
            if isinstance(value, list):
                for item in value:
                    paragraph(item)
            else:
                paragraph(value)

    contact = cv_data.get("contact") or {}
    paragraph(cv_data.get("titre_profil") or "Curriculum vitae", "CVTitle")
    paragraph(contact.get("nom"))
    paragraph(" · ".join(str(contact[key]) for key in ("email", "telephone", "adresse") if contact.get(key)))
    functional, technical = classify_competences(cv_data.get("competences", []))
    section("Compétences techniques", technical)
    section("Compétences fonctionnelles", functional)
    if cv_data.get("experiences"):
        section("Expériences", [format_experiences([exp]) for exp in cv_data["experiences"]])
    if cv_data.get("formations"):
        section("Formations", [format_formations([form]) for form in cv_data["formations"]])
    for key, title in [("certifications", "Certifications"), ("langues", "Langues"),
                       ("projets", "Projets"), ("loisirs", "Loisirs"),
                       ("disponibilite", "Disponibilité")]:
        section(title, cv_data.get(key))
    story.append(Spacer(1, 4*mm))

    def decorate(canvas, doc):
        width, height = A4
        canvas.saveState()
        canvas.setStrokeColor(ORANGE)
        canvas.setLineWidth(2)
        canvas.line(23*mm, height-15*mm, width-23*mm, height-15*mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(23*mm, 12*mm, "Curriculum vitae")
        canvas.drawRightString(width-23*mm, 12*mm, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return output_path
