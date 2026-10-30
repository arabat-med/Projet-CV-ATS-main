# Hosting configuration

These files describe a possible hosting setup. They do not prove that a production deployment is working.

## Frontend

The root [vercel.json](../vercel.json) installs and builds `Projet-Sopra-Steria-main/frontend`, publishes its `dist` directory, and directs browser routes to `index.html`.

Set `VITE_API_URL` to the actual HTTPS backend URL before building for separate hosting. The static frontend does not host Flask. Configure the frontend's actual origin in `CV_ALLOWED_ORIGINS` on the backend.

## Backend

[render.yaml](../render.yaml) and [Procfile](../Procfile) start Gunicorn with one worker and a 120-second timeout. The bundled NER model is loaded from the repository. Use Python 3.12, matching the locally verified environment, and a writable temporary data directory.

The configured health route is `/api/health`. See the [root README](../README.md#configuration) for environment variables, retention behavior, and local execution.

Direct PDF generation uses ReportLab. Edited-DOCX conversion additionally needs LibreOffice, or Pandoc with a PDF engine; neither system dependency is installed by the current hosting configuration.

## Verification scope

Local backend tests, frontend lint/build, and browser demonstrations are recorded in [VALIDATION.md](VALIDATION.md). Remote hosting, storage persistence, resource limits, and converter availability must be tested on the selected service.

Result links grant temporary access without authentication. Add appropriate access control before processing real CVs on a public service.
