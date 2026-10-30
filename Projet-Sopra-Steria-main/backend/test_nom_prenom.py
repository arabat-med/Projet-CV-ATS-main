"""Cas de noms entièrement fictifs ; aucune coordonnée issue d'un CV réel."""
import pytest
from extractors.extracteur import extraire_nom_prenom


@pytest.mark.parametrize(("text", "expected"), [
    ("Camille Exemple\nCOMPÉTENCES", "Camille Exemple"),
    ("1 rue Fictive, 00000 Ville\nCamille Exemple", "Camille Exemple"),
    ("Marie-Claire Exemple", "Marie-Claire Exemple"),
    ("François Érique Exemple", "François Érique Exemple"),
    ("Chef de Projet Développement", None),
    ("1 avenue Camille Exemple", None),
])
def test_extract_person_name(text, expected):
    assert extraire_nom_prenom(text) == expected
