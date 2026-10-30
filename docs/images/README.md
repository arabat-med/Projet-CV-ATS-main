# Authentic application screenshots

These images come from the real local application and its actual document exports. All CV content is fictional. The French filenames are retained so the existing browser verification script can regenerate the same assets.

| Image | What it shows | Provenance |
|---|---|---|
| [01-accueil.png](01-accueil.png) | Home page, light theme | Local browser, `/` |
| [02-import.png](02-import.png) | Upload form | Local browser, `/start` |
| [03-extraction.png](03-extraction.png) | Full extraction result | Real analysis of the DOCX generated from [cv-demo.txt](../../examples/cv-demo.txt) |
| [04-normalisation.png](04-normalisation.png) | Normalized JSON and export controls | Real import of [cv-ancien.json](../../examples/cv-ancien.json) |
| [05-exemple-json.png](05-exemple-json.png) | Built-in fictional JSON illustration | `/example`; not a live API result and not the extraction schema |
| [06-theme-sombre.png](06-theme-sombre.png) | Home page, dark theme | Local browser, `/` |
| [07-mobile.png](07-mobile.png) | Normalization on mobile | Local browser at 390 px viewport width |
| [08-resultat-detail.png](08-resultat-detail.png) | Extraction result component | Direct component capture after the real demo DOCX analysis |
| [09-export-pdf.png](09-export-pdf.png) | First page of the direct PDF export | Real normalized PDF, rendered with Poppler |
| [10-export-word.png](10-export-word.png) | First page of the Word export | Real normalized DOCX, converted through LibreOffice and rendered with Poppler |

Images 09 and 10 use the same fictional normalization fixture. Their layouts differ because Word generation and direct PDF composition are separate implementations. A rendered Word page is not a screenshot of a Word editor.

No image has been synthesized, retouched, or filled with invented application results. The completeness percentage visible in the extraction interface counts populated sections, not prediction accuracy or candidate quality. The home illustration is decorative.

See [the reproduction commands and exact manual capture checklist](../DEMONSTRATIONS.md). Older screenshots are not included in the published files.
