"""Régression de confusion entre nom de rue et identité, avec données fictives."""
from extractors.extracteur import extraire_nom_prenom


def test_street_name_is_not_a_person():
    text = "Camille Exemple\n1 rue Camille Exemple, 00000 Ville fictive\nalex.demo@example.invalid"
    assert extraire_nom_prenom(text) == "Alex Demo"
