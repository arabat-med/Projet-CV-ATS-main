# Frontend

Interface React 19, React Router 7, Vite 7 et Tailwind CSS 4 via le plugin Vite. Le verrou npm fixe les versions installées. Node 20.19+ sur la branche 20 ou Node 22.12+ est nécessaire.

Depuis la racine Git :

```bash
npm ci --ignore-scripts --prefix Projet-Sopra-Steria-main/frontend
npm run dev --prefix Projet-Sopra-Steria-main/frontend
```

## Pages

| Route | Comportement |
|---|---|
| `/` | Présentation et navigation |
| `/start` | Téléversement PDF texte/DOCX, résultats, JSON et exports documentaires |
| `/normalize` | Entrée JSON/DOCX, aperçu du schéma v2 et exports |
| `/example` | Présentation intégrée à données fictives, indépendante de l'API |
| `/howitworks` | Explication du traitement et de ses limites |

`src/utils/api.js` centralise l'URL API et la validation de taille/extension. `VITE_API_URL` est vide par défaut. Le proxy Vite relaie `/api` vers `127.0.0.1:5000`. Pour un frontend hébergé séparément, définir l'URL HTTPS du backend au build et son origine dans `CV_ALLOWED_ORIGINS` côté backend.

Le thème est mémorisé dans `localStorage`. La complétude affichée est la proportion de six éléments présents : nom, email, formations, expériences, compétences et langues. Elle ne mesure pas la précision de l'extraction ou la qualité d'un candidat. Aucun niveau de compétence n'est déduit graphiquement.

```bash
npm run lint --prefix Projet-Sopra-Steria-main/frontend
npm run build --prefix Projet-Sopra-Steria-main/frontend
```

Les commandes npm ci-dessus constituent le parcours d'installation et de validation ; aucun script de déploiement supplémentaire n'est nécessaire.

[Captures et vérification navigateur](../../docs/DEMONSTRATIONS.md).
