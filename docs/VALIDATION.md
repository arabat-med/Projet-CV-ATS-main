# Verification record

Local verification and publication cleanup: **30 October 2026**. Environment: Linux, Python **3.12.3**, Node.js **22.14.0**, npm **11.6.2**, and Google Chrome. Only fictional CV data was used.

## Commands tested locally

All application commands ran from the Git repository root. Temporary environments, browser captures, and generated CVs were written outside the repository. The README uses `.venv` as the conventional environment directory; verification used `/tmp/cv-readme-venv` instead.

| Command or check | Observed result |
|---|---|
| `python3 -m venv` and `python -m pip install -r Projet-Sopra-Steria-main/backend/requirements-dev.txt` | Clean virtual environment created; dependency installation succeeded |
| `python -m pip check` | No broken requirements found |
| `npm ci --ignore-scripts --prefix Projet-Sopra-Steria-main/frontend` | Lockfile installation succeeded; lifecycle scripts disabled |
| `python -m pytest -q` | **44 passed**, including the real LibreOffice conversion test; three dependency deprecation warnings |
| `npm run lint --prefix Projet-Sopra-Steria-main/frontend` | Passed |
| `npm run build --prefix Projet-Sopra-Steria-main/frontend` | Passed, without CSS warnings |
| `python Projet-Sopra-Steria-main/backend/api.py` | Bundled NER model loaded; local health endpoint returned HTTP 200 with `status: ok` |
| `npm run dev --prefix Projet-Sopra-Steria-main/frontend` | Vite served the real interface on port 5173; verification explicitly bound `127.0.0.1` |
| `python scripts/create_demo_inputs.py --output /tmp/cv-demo-inputs` | Fictional DOCX and text PDF created |
| README `curl` analysis example | HTTP request succeeded; response contained the fixture's fictional email |
| `scripts/check_browser.cjs` with Playwright and Chrome | Real DOCX/PDF upload, JSON download, normalization, document export, theme switching, and mobile navigation passed |
| DOCX conversion through `/api/cv/convert` | Actual normalized Word export converted with LibreOffice |
| Poppler rendering commands in the demo protocol | Direct PDF and converted Word PDF rendered successfully |
| Mermaid parser and local browser rendering | Architecture parsed as a flowchart and rendered as SVG |
| Local Markdown preview | README images loaded without broken image resources; diagram inspected |
| Relative documentation links and `git diff --check` | Checked |
| Screenshot and model hashes | All ten authentic gallery images and model weights preserved during publication cleanup |
| Word template metadata | Author and last-editor fields cleared; document content and layout XML parts preserved byte-for-byte |

The test invocation added `-B` and `-p no:cacheprovider` to avoid Python bytecode and pytest cache writes. The browser script wrote fresh verification images to `/tmp/cv-readme-captures`; the gallery retains the existing authentic captures. The browser tool dependencies were installed separately under `/tmp/cv-doc-tools`, not added to the project manifests.

The browser script checks theme switching; it does not test persistence across a browser restart. Persistence is implemented in the frontend's local-storage hook. The local Markdown preview is a rendering check. Repository publication is recorded by Git commits; remote CI and hosting status are separate checks.

## Not verified

- Windows/PowerShell and macOS setup or execution.
- Node 20 and other Node versions allowed by the package manifest.
- The separately installed `fr_core_news_md` fallback path.
- Pandoc with an external PDF engine.
- Successful remote GitHub Actions execution or Vercel/Render deployment.
- OCR, multilingual extraction quality, NLP precision/recall/F1, ATS compatibility, throughput, latency, or load limits.
- A complete accessibility audit or production security assessment.

PyPDF2 and Typer/Click emit deprecation warnings. Direct Python dependencies are pinned; all transitive versions are not locked. No model was retrained.

## Publication cleanup

- The root README is the main project overview; no README override exists in `.github/`.
- Duplicate Markdown pages, the redundant frontend validation shell wrapper, old screenshots, IDE metadata, placeholder assets, and obsolete nested hosting configurations are excluded from the published files. Useful technical notes and reproducible demo scripts are retained.
- Ignore rules are consolidated in the root `.gitignore`. Virtual environments, `node_modules`, build output, local CV data, and environment overrides are not published.
- `requirements.txt`, `requirements-dev.txt`, `package.json`, and `package-lock.json` remain necessary for installation, tests, and reproducible builds. Removed dependencies were unused; the existing manifests describe the actual stack.
- The GitHub Actions push trigger now targets `master`, matching the remote default branch. Pull requests also trigger the workflow. Check the repository's Actions tab for remote results.
- This record consolidates the earlier README change report. The [demo protocol](DEMONSTRATIONS.md), [gallery](images/README.md), [hosting notes](DEPLOYMENT.md), and [attribution](ATTRIBUTION.md) provide the remaining documentation.

No model was retrained and Git history was not rewritten. Earlier commits still contain legacy contact fixtures; see the [attribution and privacy notes](ATTRIBUTION.md). A personal contribution statement and project-wide reuse rights still need clarification.
