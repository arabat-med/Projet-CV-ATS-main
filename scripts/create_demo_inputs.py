"""Génère deux entrées fictives pour essayer l'application, sans CV personnel."""
import argparse
from pathlib import Path
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    lines = (Path(__file__).resolve().parent.parent / "examples/cv-demo.txt").read_text().splitlines()
    document = Document()
    document.core_properties.author = ""
    for line in lines:
        document.add_paragraph(line)
    document.save(args.output / "cv-demo.docx")
    pdf = canvas.Canvas(str(args.output / "cv-demo.pdf"), pagesize=A4)
    pdf.setTitle("CV fictif de démonstration")
    pdf.setAuthor("")
    pdf.setFont("Helvetica", 11)
    y = A4[1] - 55
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 24
    pdf.save()
    print("Entrées fictives créées dans", args.output.resolve())


if __name__ == "__main__":
    main()
