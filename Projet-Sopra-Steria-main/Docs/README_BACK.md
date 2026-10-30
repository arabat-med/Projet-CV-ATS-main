# Backend

L'API Flask est définie dans [`backend/api.py`](../backend/api.py). Lancer depuis la racine Git :

```bash
python Projet-Sopra-Steria-main/backend/api.py
```

Le parcours d'analyse lit le PDF texte avec PyPDF2 ou le DOCX avec python-docx, tableaux compris. `analyser_cv.py` extrait les contacts et dates ; `section_classifier.py` combine parsing de sections et entités de `spacy_extractor.py`. Le modèle actif est `models/cv_ner`, configurable avec `CV_NER_MODEL_PATH`.

Les sources sont supprimées après traitement. Chaque analyse possède un dossier sous `CV_DATA_DIR`, avec un identifiant aléatoire et une expiration enregistrée dans `job.json`. Le JSON et le PDF restent disponibles pendant `CV_RETENTION_SECONDS`, une heure par défaut. Les requêtes déclenchent la suppression des dossiers expirés. Le nettoyage différé n'est pas une garantie d'effacement immédiat à l'expiration.

Le téléchargement Word génère le document en mémoire depuis le JSON. Les exports PDF directs passent par ReportLab, avec pagination. La route de conversion d'un Word réédité appelle LibreOffice ou Pandoc ; elle renvoie 503 en l'absence de conversion possible, sans produire silencieusement un document textuel différent.

Les modules `enhanced_extractor.py` et `heuristic_rules.py` sont des expérimentations conservées, non appelées par l'API. Les modèles NER et TextCat de `models/cv_pipeline` ne sont pas chargés automatiquement.

Le script CLI `analyser_cv.py` constitue un parcours distinct : il traite les DOCX placés dans `backend/data/input` et écrit uniquement les extractions regex dans `backend/data/output`. Il ne remplace pas l'analyse structurée de l'API et conserve ses entrées locales.

## Entraînement

Les modèles fournis ont des métadonnées spaCy 3.8. Le corpus est dans `training/training_data.py`. Le rapport sauvegardé décrit l'entraînement, sans précision mesurée sur un jeu indépendant.

Pour réentraîner le modèle utilisé par l'API, depuis `backend/`, dans un environnement dédié :

```bash
python -m spacy download fr_core_news_md
python training/train_ner.py --output models/cv_ner --iterations 30
```

Cette commande **remplace le modèle cible** : conserver une copie ou choisir un autre `--output` puis définir `CV_NER_MODEL_PATH`. Redémarrer l'API pour charger le nouveau modèle. Aucun réentraînement n'a été effectué lors de la remise en état.

`train_cv_pipeline.py` entraîne séparément NER/TextCat sous `models/cv_pipeline`. Il ne met pas à jour le modèle actif par défaut. Les distributions de modèles restent volumineuses ; leur consolidation nécessite une décision sur les expérimentations à conserver.

Voir le [README principal](../../README.md) pour installation, configuration, routes et limites.
