# Normalisation des CV

`backend/extractors/version_mapper.py` accepte le JSON d'extraction, le format historique éventuellement enveloppé dans `resultats_spacy`, et le résultat d'une normalisation précédente. Un second passage conserve le même résultat. L'objet d'entrée n'est pas modifié.

## Structure effective

```json
{
  "meta": {"version": "2.0"},
  "contact": {"nom": "Camille EXEMPLE", "email": "demo@example.invalid", "telephone": "", "adresse": ""},
  "header": {"titre_document": "CURRICULUM VITAE", "role": "", "initiales": "CE"},
  "competences": [],
  "competences_techniques": ["Python"],
  "competences_fonctionnelles": [],
  "experiences": [{"titre": "Une expérience", "missions": ["Une mission"], "environnement": "Python"}],
  "formations": [],
  "langues": [],
  "projets": [],
  "certifications": [],
  "loisirs": []
}
```

Les expériences déjà structurées avec `entreprise`, `poste`, `dates` et `description` sont conservées comme objets. Les anciens blocs de lignes sont regroupés sous `titre`, `missions` et `environnement`. Les formations peuvent rester des objets ou des lignes historiques. Les champs additionnels du CV sont préservés.

Une liste non catégorisée reste dans `competences`. Les listes catégorisées et l'ancien objet `competences.techniques/fonctionnelles` sont pris en compte. Aucune compétence absente n'est inventée.

`convert_v2_to_old_format` adapte ces structures aux générateurs : nom et coordonnées sont conservés, les missions deviennent un texte, les formations historiques deviennent des entrées documentaires. Le titre historique complet est conservé comme intitulé ; aucune entreprise ou période n'est déduite de force.

## API

- `POST /api/cv/normalize` : `{"cv_data": {...}}` ou champ multipart `file` JSON/DOCX.
- `POST /api/cv/normalize-batch` : `{"cvs": [...]}`, au plus 100 entrées, résultats individuels et synthèse.
- `POST /api/cv/normalize/docx` et `/api/cv/normalize/pdf` : mêmes entrées, fichier en réponse.

Les métadonnées comptent les rubriques et compétences uniques pour les deux modes d'entrée. Les DOCX historiques doivent contenir des titres de section reconnus, par exemple « Compétences techniques », « Expériences », « Formations » et « Langues ». Paragraphes et tableaux sont lus ; une structure arbitraire peut nécessiter le parcours d'extraction classique.

Exemple d'entrée : [`examples/cv-ancien.json`](../../examples/cv-ancien.json). Tests de conservation et d'idempotence : `backend/test_normalization.py`.

## Interface

La page `frontend/src/pages/Normalize/Normalize.jsx` accepte un JSON ou un DOCX. Elle appelle `/api/cv/normalize`, affiche les compteurs et le résultat JSON, puis transmet ce résultat aux routes d'export Word/PDF. Les appels passent par `src/utils/api.js` et les exports JSON sont créés côté navigateur. Le parcours réel est vérifié dans `scripts/check_browser.cjs` avec l'entrée fictive fournie.
