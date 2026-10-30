"""Fixtures exclusivement fictives ; chaque test écrit dans son répertoire temporaire."""
from io import BytesIO

from docx import Document
import pytest


@pytest.fixture
def sample_cv():
    return {
        "contact": {"nom": "Camille EXEMPLE", "email": "demo@example.invalid", "telephone": "", "adresse": ""},
        "titre_profil": "Développeur Python",
        "experiences": [{"entreprise": "Entreprise Démonstration", "poste": "Développeur Python",
                         "dates": "2022 - 2024", "description": "Création d'un outil de démonstration.",
                         "environnement_technique": "Python, Flask"}],
        "formations": [{"etablissement": "Université Exemple", "diplome": "Master Informatique", "dates": "2020 - 2022"}],
        "competences": ["Python", "React", "Communication"], "langues": ["Français", "Anglais"],
        "projets": ["Projet fictif"], "certifications": [], "loisirs": [],
    }


@pytest.fixture
def sample_docx():
    document = Document()
    for line in ["Camille EXEMPLE", "Développeur Python", "demo@example.invalid", "FORMATIONS",
                 "2020 - 2022 | Université Exemple | Master Informatique", "EXPERIENCES",
                 "2022 - 2024 | Entreprise Démonstration | Développeur Python",
                 "- Création d'un outil de démonstration.", "COMPÉTENCES", "Python, React", "LANGUES", "Français, Anglais"]:
        document.add_paragraph(line)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    from api import app
    monkeypatch.setitem(app.config, "TESTING", True)
    monkeypatch.setitem(app.config, "DATA_ROOT", tmp_path / "jobs")
    with app.test_client() as client:
        yield client
