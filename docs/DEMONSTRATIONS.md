# Authentic demonstrations

The numbered images in [images/](images/README.md) were captured from the real local Flask/Vite application in Google Chrome. The browser script neither intercepts nor replaces API responses. The interface is in French; the documentation is in English.

All demo CV content is fictional. The inputs are [cv-demo.txt](../examples/cv-demo.txt), from which the demo DOCX and text PDF are created, and [cv-ancien.json](../examples/cv-ancien.json), the normalization fixture. The email address is `demo@example.invalid`.

All published screenshots are organized in `docs/images/`. Older screenshots were excluded during publication cleanup; the current gallery uses only the verified fictional fixtures. The decorative home-page illustration is not an extraction result.

## Reproduce the browser workflow

Install the application dependencies and start both servers as described in the [root README](../README.md#installation-and-local-run). Then run these commands from the repository root, with the Python environment active:

```bash
python scripts/create_demo_inputs.py --output /tmp/cv-demo-inputs
npm install --prefix /tmp/cv-browser --no-save --ignore-scripts playwright
NODE_PATH=/tmp/cv-browser/node_modules node scripts/check_browser.cjs /tmp/cv-demo-inputs docs/images
```

This is the Linux protocol used for the existing browser captures, with Google Chrome installed. The last command overwrites images 01–08 with new authentic captures. Playwright is installed outside the repository and is not a runtime dependency. `CV_BASE_URL` changes the target URL; `CV_BROWSER_CHANNEL` selects the browser channel. Adapt temporary paths and shell syntax for other systems; those variants have not been verified.

The script exercises real DOCX and text-PDF uploads, JSON download, legacy JSON normalization, DOCX/PDF export, theme switching, and mobile navigation. It checks the returned fictional email, HTTP responses, absence of page errors, and horizontal overflow on the mobile normalization page. It does not provide an NLP quality benchmark, a full accessibility audit, or a load test. Theme persistence is implemented with local storage; the script checks switching, not persistence across a browser restart.

## Reproduce document renders

Images 09 and 10 are renders of actual normalization exports. The browser workflow saves `normalise.pdf` and `normalise.docx` in the selected temporary input directory.

Render the direct ReportLab PDF with Poppler:

```bash
pdftoppm -scale-to 1600 -png \
  /tmp/cv-demo-inputs/normalise.pdf /tmp/cv-demo-inputs/pdf-direct
```

Convert the generated Word document through the real API, with LibreOffice installed:

```bash
curl --fail -F 'file=@/tmp/cv-demo-inputs/normalise.docx' \
  http://127.0.0.1:5000/api/cv/convert \
  --output /tmp/cv-demo-inputs/word-render.pdf
pdftoppm -scale-to 1600 -png \
  /tmp/cv-demo-inputs/word-render.pdf /tmp/cv-demo-inputs/word-render
```

Inspect every rendered page before selecting a PNG for the gallery. The existing images show the first page of each real export and have not been retouched. Word layout can vary with the converter and installed fonts; it is distinct from the direct ReportLab layout.

## Manual capture checklist

The current README already has authentic captures, so no placeholder or fabricated image is needed. To refresh them manually, use only the fictional fixtures:

| Image | Page or action to capture |
|---|---|
| `01-accueil.png` | `/`, light theme, desktop viewport 1440 × 1000 |
| `02-import.png` | `/start`, before selecting a file |
| `03-extraction.png` | `/start`, after analyzing the generated `cv-demo.docx`; full page |
| `04-normalisation.png` | `/normalize`, after importing `examples/cv-ancien.json`; full result |
| `05-exemple-json.png` | `/example`, select **Format JSON**; label it as a built-in illustration |
| `06-theme-sombre.png` | `/`, dark theme |
| `07-mobile.png` | `/normalize`, viewport width 390 px; verify navigation and overflow |
| `08-resultat-detail.png` | The extraction result component from step 3, captured directly |
| `09-export-pdf.png` | First rendered page of the actual normalized PDF export |
| `10-export-word.png` | First rendered page of the actual normalized Word export converted to PDF |

Do not include real CVs, private file paths, credentials, or unrelated browser content. Keep captions explicit about which input and workflow produced the image.
