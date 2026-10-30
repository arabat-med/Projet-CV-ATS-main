# Intégration continue

Le workflow actif est [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), à la racine Git. Il s'applique aux push sur `master` et aux pull requests, avec une permission de lecture du contenu.

- Backend : Ubuntu, Python 3.12, installation de `requirements-dev.txt`, puis `python -m pytest -q` depuis la racine.
- Frontend : Ubuntu, Node 22.14, installation avec `npm ci --ignore-scripts`, lint et build dans `Projet-Sopra-Steria-main/frontend`.

Le modèle NER est fourni dans le dépôt ; le workflow ne télécharge pas de modèle de base. Le test système LibreOffice est ignoré si le binaire est absent. Les autres tests utilisent des répertoires temporaires et des données fictives.

La configuration a été vérifiée localement ; aucun résultat GitHub Actions distant n'est revendiqué. Les vérifications navigateur nécessitent des serveurs locaux et Chrome, selon le [protocole](../../docs/DEMONSTRATIONS.md).
