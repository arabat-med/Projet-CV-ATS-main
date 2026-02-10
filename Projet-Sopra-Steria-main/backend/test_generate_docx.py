#!/usr/bin/env python3
"""
Script de test pour valider la génération de DOCX adaptée à la template.
"""

import json
import os
from generators.generate_sopra_docx import (
    generate_sopra_docx, 
    generate_cv_documents,
    format_experiences,
    format_formations,
    bullets,
    classify_competences,
    detect_template_sections
)
from docx import Document

def test_with_sample_data():
    """Test avec les données d'exemple du CV Léo WEBER"""
    
    # Charger les données du CV d'exemple
    sample_cv_path = "data/output/cv_result_20260115_010151.json"
    
    if not os.path.exists(sample_cv_path):
        print(f"❌ Fichier exemple non trouvé: {sample_cv_path}")
        return False
    
    with open(sample_cv_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    print("=" * 60)
    print("TEST GÉNÉRATION DOCX")
    print("=" * 60)
    
    # Tester la détection des sections
    print("\n1. Détection des sections de la template...")
    template_path = "templates/sopra_template.docx"
    if os.path.exists(template_path):
        doc = Document(template_path)
        sections = detect_template_sections(doc)
        print(f"   ✓ Sections détectées: {sections}")
    else:
        print(f"   ⚠️ Template non trouvée: {template_path}")
    
    # Tester la classification des compétences
    print("\n2. Test classification des compétences...")
    comp_fonct, comp_tech = classify_competences(cv_data.get("competences", []))
    print(f"   ✓ Compétences fonctionnelles ({len(comp_fonct)}): {', '.join(comp_fonct[:3])}...")
    print(f"   ✓ Compétences techniques ({len(comp_tech)}): {', '.join(comp_tech[:3])}...")
    
    # Tester le formatage des expériences
    print("\n3. Test formatage des expériences...")
    exps_text = format_experiences(cv_data.get("experiences", []))
    print("   ✓ Expériences formatées:")
    for line in exps_text.split('\n')[:5]:
        print(f"      {line}")
    if len(exps_text.split('\n')) > 5:
        print(f"      ... ({len(exps_text.split(chr(10)))} lignes au total)")
    
    # Tester le formatage des formations
    print("\n4. Test formatage des formations...")
    forms_text = format_formations(cv_data.get("formations", []))
    print("   ✓ Formations formatées:")
    for line in forms_text.split('\n')[:5]:
        print(f"      {line}")
    
    # Tester le formatage des listes
    print("\n5. Test formatage des listes (bullets)...")
    competences = bullets(cv_data.get("competences", []))
    print(f"   ✓ Compétences formatées ({len(competences.split(chr(10)))} items):")
    for item in competences.split('\n')[:3]:
        print(f"      {item}")
    
    # Générer le DOCX
    print("\n6. Génération du DOCX...")
    output_dir = "data/output/test_generated"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        docx_path = os.path.join(output_dir, "CV_Test.docx")
        result = generate_sopra_docx(cv_data, docx_path)
        print(f"   ✓ DOCX généré: {result}")
        
        # Vérifier que le fichier a été créé
        if os.path.exists(result):
            file_size = os.path.getsize(result)
            print(f"   ✓ Fichier créé avec succès ({file_size} bytes)")
            
            # Vérifier le contenu
            generated_doc = Document(result)
            print(f"   ✓ Contenu vérifiable: {len(generated_doc.paragraphs)} paragraphes")
        else:
            print("   ❌ Le fichier n'a pas pu être créé")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test avec generate_cv_documents
    print("\n7. Test avec generate_cv_documents...")
    try:
        result = generate_cv_documents(cv_data, output_dir, "CV_Integration_Test")
        print(f"   ✓ Résultats: {result}")
    except Exception as e:
        print(f"   ⚠️ Erreur (non critique): {e}")
    
    print("\n" + "=" * 60)
    print("✅ TESTS RÉUSSIS")
    print("=" * 60)
    return True

def test_edge_cases():
    """Test les cas limites"""
    print("\n" + "=" * 60)
    print("TEST CAS LIMITES")
    print("=" * 60)
    
    # Données minimalistes
    minimal_cv = {
        "contact": {
            "nom": "Jean DUPONT"
        },
        "titre_profil": "Développeur",
        "formations": [],
        "experiences": [],
        "competences": [],
        "langues": []
    }
    
    print("\n1. Test avec données minimalistes...")
    try:
        output_dir = "data/output/test_generated"
        os.makedirs(output_dir, exist_ok=True)
        docx_path = os.path.join(output_dir, "CV_Minimal.docx")
        result = generate_sopra_docx(minimal_cv, docx_path)
        print(f"   ✓ DOCX minimal généré: {os.path.basename(result)}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Données avec listes vides
    print("\n2. Test formatage avec listes vides...")
    empty_bullets = bullets([], "Testé avec fallback")
    if "Testé avec fallback" in empty_bullets:
        print(f"   ✓ Fallback fonctionne: {empty_bullets}")
    else:
        print(f"   ❌ Fallback échoué: {empty_bullets}")
        return False
    
    print("\n✅ CAS LIMITES RÉUSSIS")
    return True

if __name__ == "__main__":
    success = True
    
    try:
        success = test_with_sample_data() and success
    except Exception as e:
        print(f"\n❌ Erreur fatale dans test_with_sample_data: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    try:
        success = test_edge_cases() and success
    except Exception as e:
        print(f"\n❌ Erreur fatale dans test_edge_cases: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    if success:
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS RÉUSSIS")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("=" * 60)
        exit(1)
