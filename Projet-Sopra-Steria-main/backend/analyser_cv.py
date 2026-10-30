"""
Script pour extraire les informations d'un CV
"""
import os
import json
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pathlib import Path
from extractors.extracteur import extraire_dates, extraire_email, extraire_telephone, extraire_adresse

def iter_document_text(document):
    """Parcourt paragraphes et cellules, tableaux imbriqués compris, dans l'ordre XML."""
    element = document.element.body if hasattr(document, "element") else document._tc
    for child in element.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document).text
        elif child.tag.endswith("}tbl"):
            for row in Table(child, document).rows:
                seen = set()
                for cell in row.cells:
                    if cell._tc not in seen:
                        seen.add(cell._tc)
                        yield from iter_document_text(cell)


def lire_cv_docx(chemin_fichier):
    """Lit un DOCX ou un flux binaire, tableaux inclus."""
    return "\n".join(iter_document_text(Document(chemin_fichier)))

def extraire_infos_cv(texte_cv):
    """Retourne les données brutes extraites d'un texte de CV."""
    return {
        "dates": extraire_dates(texte_cv),
        "emails": extraire_email(texte_cv),
        "telephones": extraire_telephone(texte_cv),
        "adresses": extraire_adresse(texte_cv)
    }


def analyser_cv():
    base = Path(__file__).resolve().parent
    dossier_input = base / "data/input"
    dossier_output = base / "data/output"

    os.makedirs(dossier_output, exist_ok=True)

    fichiers_cv = [f.name for f in dossier_input.glob('*.docx')]
    if not fichiers_cv:
        print("Aucun CV (.docx) trouvé dans data/input")
        return

    for fichier in fichiers_cv:
        chemin_cv = os.path.join(dossier_input, fichier)
        texte_cv = lire_cv_docx(chemin_cv)

        # ➜ On utilise la fonction unique
        resultats = extraire_infos_cv(texte_cv)

        nom_json = os.path.splitext(fichier)[0] + "_resultats.json"
        chemin_sortie = os.path.join(dossier_output, nom_json)

        with open(chemin_sortie, 'w', encoding='utf-8') as f:
            json.dump(resultats, f, indent=2, ensure_ascii=False)

        print("Analyse OK →", chemin_sortie)


if __name__ == "__main__":
    analyser_cv()
