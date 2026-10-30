"""API locale d'extraction, normalisation et génération de CV."""
from contextlib import contextmanager
from datetime import datetime, timezone
from io import BytesIO
import json
import logging
import os
from pathlib import Path
import re
import secrets
import shutil
from tempfile import TemporaryDirectory
import time
from zipfile import BadZipFile
from docx.opc.exceptions import PackageNotFoundError

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from analyser_cv import lire_cv_docx, extraire_infos_cv
from extractors.pdf_to_docx import convert_pdf_to_docx
from extractors.section_classifier import build_structured_json
from extractors.version_mapper import normalize_old_cv_to_new, convert_v2_to_old_format
from generators.generate_sopra_docx import generate_sopra_docx
from generators.pdf_sopra_profile import generate_sopra_profile_pdf
from generators.docx_to_pdf import convert_docx_to_pdf, ConversionUnavailable

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config.update(
    DATA_ROOT=Path(os.environ.get("CV_DATA_DIR", str(BASE_DIR / "data" / "jobs"))).resolve(),
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    RETENTION_SECONDS=int(os.environ.get("CV_RETENTION_SECONDS", "3600")),
)
logging.basicConfig(level=logging.INFO)
CORS(app, resources={r"/api/*": {
    "origins": [origin.strip() for origin in os.environ.get(
        "CV_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()],
    "methods": ["GET", "POST"],
}})
TOKEN = re.compile(r"^[a-f0-9]{48}$")


def _data_root():
    return Path(app.config["DATA_ROOT"])


@app.before_request
def cleanup_expired_jobs():
    """L'expiration interdit l'accès ; la suppression est déclenchée par les requêtes."""
    root = _data_root()
    if not root.exists():
        return
    for folder in root.iterdir():
        if not TOKEN.fullmatch(folder.name) or not folder.is_dir() or folder.is_symlink():
            continue
        try:
            metadata = json.loads((folder / "job.json").read_text())
            if metadata["expires_at"] <= time.time():
                shutil.rmtree(folder)
        except FileNotFoundError:
            # Un autre worker peut avoir terminé la suppression.
            continue
        except (OSError, ValueError, KeyError):
            app.logger.warning("Nettoyage d'un traitement impossible")


@app.after_request
def prevent_caching(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.errorhandler(HTTPException)
def http_error(error):
    messages = {400: "Requête invalide", 404: "Document introuvable ou expiré",
                405: "Méthode non autorisée", 413: "Fichier trop volumineux (limite : 10 Mio)"}
    return jsonify(success=False, error=messages.get(error.code, error.name)), error.code


@app.errorhandler(Exception)
def unexpected_error(error):
    app.logger.exception("Échec du traitement")
    return jsonify(success=False, error="Le traitement a échoué. Vérifiez le document fourni."), 500


@app.errorhandler(BadZipFile)
@app.errorhandler(PackageNotFoundError)
def invalid_word_document(error):
    return jsonify(success=False, error="Document DOCX invalide ou endommagé"), 400


@contextmanager
def new_job():
    root = _data_root()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    token = secrets.token_hex(24)
    folder = root / token
    folder.mkdir(mode=0o700)
    (folder / "job.json").write_text(json.dumps({
        "expires_at": time.time() + app.config["RETENTION_SECONDS"]}), encoding="utf-8")
    try:
        yield token, folder
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise


def _stored_job(filename):
    token = filename.rsplit(".", 1)[0]
    if not TOKEN.fullmatch(token):
        return None
    folder = _data_root() / token
    try:
        metadata = json.loads((folder / "job.json").read_text())
        return folder if metadata["expires_at"] > time.time() else None
    except (OSError, ValueError, KeyError):
        return None


def _upload(extensions):
    file = request.files.get("file")
    if file is None or not file.filename:
        raise ValueError("Sélectionnez un fichier")
    extension = Path(file.filename).suffix.lower()
    if extension not in extensions:
        raise ValueError("Formats acceptés : " + ", ".join(sorted(extensions)))
    return file, extension


def _normalization_input():
    if request.is_json:
        body = request.get_json()
        if not isinstance(body, dict) or not isinstance(body.get("cv_data"), dict) or not body["cv_data"]:
            raise ValueError('Le champ "cv_data" doit être un objet JSON non vide')
        return normalize_old_cv_to_new(body["cv_data"])
    file, extension = _upload({".json", ".docx"})
    if extension == ".json":
        return normalize_old_cv_to_new(json.load(file.stream))
    return normalize_old_cv_to_new({}, docx_path=file.stream)


def _metadata(cv):
    generic = cv.get("competences", [])
    generic = generic if isinstance(generic, list) else []
    skills = generic + cv["competences_techniques"] + cv["competences_fonctionnelles"]
    return {
        "version_cible": cv["meta"]["version"],
        "nb_experiences": len(cv["experiences"]), "nb_formations": len(cv["formations"]),
        "nb_competences": len({json.dumps(skill, sort_keys=True) for skill in skills}),
        "nb_langues": len(cv["langues"]),
    }


def _download_bytes(buffer, extension, filename="cv"):
    buffer.seek(0)
    mimetypes = {"docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                 "pdf": "application/pdf"}
    return send_file(buffer, mimetype=mimetypes[extension], as_attachment=True,
                     download_name=f"{filename}.{extension}", max_age=0)


@app.get("/health")
@app.get("/api/health")
def health_check():
    return jsonify(status="ok", timestamp=datetime.now(timezone.utc).isoformat())


@app.post("/api/cv/analyze")
def analyze_cv():
    try:
        file, extension = _upload({".pdf", ".docx"})
        with new_job() as (token, folder):
            source = folder / f"source{extension}"
            converted = folder / "source_converted.docx"
            try:
                file.save(source)
                if extension == ".pdf":
                    if not convert_pdf_to_docx(str(source), str(converted)):
                        raise ValueError("PDF illisible : une couche texte est nécessaire (OCR non pris en charge)")
                    source = converted
                text = lire_cv_docx(source)
                if not text.strip():
                    raise ValueError("Le document ne contient pas de texte exploitable")
                raw = extraire_infos_cv(text)
                results = build_structured_json(raw["emails"], raw["telephones"], raw["adresses"], raw["dates"], text)
                generate_sopra_profile_pdf(results, folder / "cv.pdf")
                (folder / "cv.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            finally:
                for path in folder.glob("source*"):
                    path.unlink(missing_ok=True)
            results.update(json_filename=f"{token}.json", pdf_filename=f"{token}.pdf")
            return jsonify(results)
    except ValueError as error:
        return jsonify(success=False, error=str(error)), 400


@app.get("/api/cv/docx/<filename>")
def download_docx(filename):
    folder = _stored_job(filename)
    if folder is None or not (folder / "cv.json").is_file():
        return jsonify(error="Document introuvable ou expiré"), 404
    data = json.loads((folder / "cv.json").read_text(encoding="utf-8"))
    buffer = BytesIO()
    generate_sopra_docx(data, buffer)
    return _download_bytes(buffer, "docx")


@app.get("/api/cv/pdf/<filename>")
def download_pdf(filename):
    folder = _stored_job(filename)
    if folder is None or not (folder / "cv.pdf").is_file():
        return jsonify(error="Document introuvable ou expiré"), 404
    return _download_bytes(BytesIO((folder / "cv.pdf").read_bytes()), "pdf")


@app.post("/api/cv/convert")
def convert_docx_to_pdf_route():
    try:
        file, _ = _upload({".docx"})
        with TemporaryDirectory(prefix="cv-conversion-") as directory:
            source, target = Path(directory) / "source.docx", Path(directory) / "cv.pdf"
            file.save(source)
            convert_docx_to_pdf(source, target)
            buffer = BytesIO(target.read_bytes())
        return _download_bytes(buffer, "pdf", "cv_modifie")
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except ConversionUnavailable:
        return jsonify(error="Conversion indisponible : installez LibreOffice (soffice) ou Pandoc avec un moteur PDF."), 503


@app.post("/api/cv/normalize")
def normalize_cv():
    try:
        cv = _normalization_input()
        return jsonify(success=True, cv_normalized=cv, metadata=_metadata(cv))
    except (ValueError, UnicodeError) as error:
        return jsonify(success=False, error=str(error)), 400


@app.post("/api/cv/normalize-batch")
def normalize_cv_batch():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("cvs"), list):
        return jsonify(success=False, error='Le champ "cvs" doit être une liste'), 400
    if len(body["cvs"]) > 100:
        return jsonify(success=False, error="Limite : 100 CV par requête"), 400
    results = []
    for cv in body["cvs"]:
        try:
            results.append({"success": True, "cv_normalized": normalize_old_cv_to_new(cv)})
        except ValueError as error:
            results.append({"success": False, "error": str(error)})
    successes = sum(item["success"] for item in results)
    return jsonify(success=successes == len(results), results=results,
                   summary={"total": len(results), "success": successes, "errors": len(results) - successes})


@app.post("/api/cv/normalize/docx")
@app.post("/api/cv/normalize/pdf")
def normalize_and_export():
    try:
        data = convert_v2_to_old_format(_normalization_input())
        buffer = BytesIO()
        extension = request.path.rsplit("/", 1)[1]
        if extension == "docx":
            generate_sopra_docx(data, buffer)
        else:
            generate_sopra_profile_pdf(data, buffer)
        return _download_bytes(buffer, extension, "cv_normalise")
    except (ValueError, UnicodeError) as error:
        return jsonify(error=str(error)), 400


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "5000")), debug=False)
