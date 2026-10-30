"""
Script d'entraînement du TextCategorizer spaCy pour la classification de sections CV.

Ce script:
1. Charge le modèle fr_core_news_md existant
2. Ajoute un composant TextCategorizer multi-label
3. Entraîne avec les données de sections annotées
4. Sauvegarde le modèle entraîné

Usage:
    python train_textcat.py [--iterations 20] [--output models/cv_textcat]
"""

import os
import sys
import random
import json
from pathlib import Path
from datetime import datetime

import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from training.training_data import TEXTCAT_TRAINING_DATA, SECTION_CATEGORIES


def create_textcat_examples(nlp, training_data):
    """Convertit les données d'entraînement en objets Example spaCy."""
    examples = []
    for text, annotations in training_data:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, annotations)
        examples.append(example)
    return examples


def train_textcat(
    base_model: str = "fr_core_news_md",
    output_dir: str = None,
    n_iter: int = 20,
    dropout: float = 0.2
):
    """
    Entraîne le TextCategorizer avec les données annotées.
    
    Args:
        base_model: Modèle spaCy de base à utiliser
        output_dir: Dossier de sortie pour le modèle entraîné
        n_iter: Nombre d'itérations d'entraînement
        dropout: Taux de dropout
    
    Returns:
        Le modèle entraîné
    """
    print(f"📦 Chargement du modèle de base '{base_model}'...")
    try:
        nlp = spacy.load(base_model)
    except OSError:
        print(f"Modèle '{base_model}' non trouvé. Téléchargement...")
        raise RuntimeError("Modèle de base absent : installez-le explicitement avec python -m spacy download fr_core_news_md")
    
    # Ajouter le TextCategorizer
    print("\n🏷️ Configuration du TextCategorizer...")
    
    if "textcat_multilabel" in nlp.pipe_names:
        textcat = nlp.get_pipe("textcat_multilabel")
    else:
        # Utiliser textcat_multilabel pour permettre plusieurs catégories
        textcat = nlp.add_pipe("textcat_multilabel", last=True)
    
    # Ajouter les labels
    for label in SECTION_CATEGORIES:
        textcat.add_label(label)
        print(f"   + {label}")
    
    # Préparer les exemples
    print(f"\n📚 Préparation de {len(TEXTCAT_TRAINING_DATA)} exemples...")
    examples = create_textcat_examples(nlp, TEXTCAT_TRAINING_DATA)
    
    # Désactiver les autres composants
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "textcat_multilabel"]
    
    # Entraînement
    print(f"\n🚀 Début de l'entraînement ({n_iter} itérations)...")
    print("-" * 50)
    
    with nlp.disable_pipes(*other_pipes):
        nlp.initialize(lambda: examples)
        
        for iteration in range(n_iter):
            random.shuffle(examples)
            losses = {}
            
            batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
            
            for batch in batches:
                nlp.update(batch, drop=dropout, losses=losses)
            
            if (iteration + 1) % 5 == 0 or iteration == 0:
                loss_val = losses.get("textcat_multilabel", 0)
                print(f"   Itération {iteration + 1:3d}/{n_iter}: loss = {loss_val:.4f}")
    
    print("-" * 50)
    print("✓ Entraînement terminé!")
    
    # Sauvegarder
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        nlp.to_disk(output_path)
        print(f"\n💾 Modèle sauvegardé dans: {output_path}")
        
        meta = {
            "base_model": base_model,
            "trained_on": datetime.now().isoformat(),
            "iterations": n_iter,
            "categories": SECTION_CATEGORIES,
            "examples_count": len(TEXTCAT_TRAINING_DATA)
        }
        with open(output_path / "training_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    
    return nlp


def test_model(nlp, test_texts=None):
    """Teste le modèle sur des textes exemples."""
    if test_texts is None:
        test_texts = [
            "Marie DUPONT\n06 12 34 56 78\nmarie@example.invalid",
            "FORMATION\n2020-2023: Master Data Science - Polytechnique",
            "EXPÉRIENCE\nDéveloppeur Python chez Google (2019-2022)",
            "COMPÉTENCES: Python, Java, Docker, Kubernetes",
            "Langues: Français natif, Anglais courant",
            "LOISIRS: Voyages, Photographie, Sport"
        ]
    
    print("\n🧪 Test du modèle:")
    print("=" * 60)
    
    for text in test_texts:
        doc = nlp(text)
        cats = doc.cats
        
        # Trier par score décroissant
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
        top_cat = sorted_cats[0]
        
        print(f"\nTexte: {text[:50]}...")
        print(f"   Catégorie: {top_cat[0]} ({top_cat[1]:.2%})")
        
        # Afficher les autres catégories significatives
        for cat, score in sorted_cats[1:3]:
            if score > 0.1:
                print(f"            {cat} ({score:.2%})")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Entraînement TextCat spaCy pour sections CV")
    parser.add_argument("--iterations", "-n", type=int, default=20,
                        help="Nombre d'itérations (défaut: 20)")
    parser.add_argument("--output", "-o", type=str, default="models/cv_textcat",
                        help="Dossier de sortie (défaut: models/cv_textcat)")
    parser.add_argument("--base-model", "-m", type=str, default="fr_core_news_md",
                        help="Modèle de base (défaut: fr_core_news_md)")
    parser.add_argument("--test", "-t", action="store_true",
                        help="Tester le modèle après entraînement")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   ENTRAÎNEMENT TEXTCAT POUR SECTIONS CV")
    print("=" * 60)
    
    output_dir = Path(__file__).parent.parent / args.output
    
    nlp = train_textcat(
        base_model=args.base_model,
        output_dir=str(output_dir),
        n_iter=args.iterations
    )
    
    if args.test:
        test_model(nlp)
    
    print("\n✅ Terminé!")


if __name__ == "__main__":
    main()
