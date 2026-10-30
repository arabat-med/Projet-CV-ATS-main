from io import BytesIO
import json
import re
from docx import Document
from PyPDF2 import PdfReader
from analyser_cv import iter_document_text
import pytest


def test_health_and_validation(client):
    assert client.get("/health").status_code == 200
    assert client.get("/api/health").json["status"] == "ok"
    assert client.post("/api/cv/analyze").status_code == 400
    assert client.post("/api/cv/normalize", json={"cv_data": []}).status_code == 400
    assert client.post("/api/cv/normalize-batch", json={"cvs": {}}).status_code == 400


def test_analyze_download_and_source_cleanup(client, sample_docx):
    first = client.post("/api/cv/analyze", data={"file": (BytesIO(sample_docx), "same.docx")})
    second = client.post("/api/cv/analyze", data={"file": (BytesIO(sample_docx), "same.docx")})
    assert first.status_code == second.status_code == 200
    data = first.json
    assert data["contact"]["email"] == "demo@example.invalid"
    assert len(data["formations"]) == 1
    assert len(data["experiences"]) == 1
    assert data["json_filename"] != second.json["json_filename"]
    assert re.fullmatch(r"[a-f0-9]{48}\.pdf", data["pdf_filename"])
    folder = client.application.config["DATA_ROOT"] / data["json_filename"].removesuffix(".json")
    assert not list(folder.glob("source*"))
    pdf = client.get("/api/cv/pdf/" + data["pdf_filename"])
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")
    word = client.get("/api/cv/docx/" + data["json_filename"].removesuffix(".json"))
    assert word.status_code == 200
    assert "{{" not in "\n".join(iter_document_text(Document(BytesIO(word.data))))
    assert pdf.headers["Cache-Control"] == "no-store"


def test_expired_and_unknown_documents_are_unavailable(client, sample_docx):
    response = client.post("/api/cv/analyze", data={"file": (BytesIO(sample_docx), "demo.docx")})
    name = response.json["pdf_filename"]
    folder = client.application.config["DATA_ROOT"] / name.removesuffix(".pdf")
    (folder / "job.json").write_text(json.dumps({"expires_at": 0}))
    assert client.get("/api/cv/pdf/" + name).status_code == 404
    assert not folder.exists()
    assert client.get("/api/cv/docx/CV_Camille_Exemple").status_code == 404


def test_normalization_metadata_and_exports_preserve_data(client, sample_cv):
    source = {**sample_cv, "competences_techniques": ["Python"]}
    response = client.post("/api/cv/normalize", json={"cv_data": source})
    assert response.status_code == 200
    normalized = response.json["cv_normalized"]
    assert response.json["metadata"]["nb_competences"] == 3
    assert response.json["metadata"]["version_cible"] == normalized["meta"]["version"]
    for extension in ("docx", "pdf"):
        result = client.post("/api/cv/normalize/" + extension, json={"cv_data": normalized})
        assert result.status_code == 200
        if extension == "docx":
            text = "\n".join(iter_document_text(Document(BytesIO(result.data))))
        else:
            text = "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(result.data)).pages)
        assert "demo@example.invalid" in text
        assert "Entreprise Démonstration" in text
        assert "Création" in text


def test_multipart_json_normalization_has_same_metadata(client, sample_cv):
    direct = client.post("/api/cv/normalize", json={"cv_data": sample_cv})
    upload = client.post("/api/cv/normalize", data={"file": (BytesIO(json.dumps(sample_cv).encode()), "demo.JSON")})
    assert upload.status_code == 200
    assert upload.json == direct.json


def test_batch_reports_invalid_items(client, sample_cv):
    response = client.post("/api/cv/normalize-batch", json={"cvs": [sample_cv, 42]})
    assert response.status_code == 200
    assert response.json["summary"] == {"total": 2, "success": 1, "errors": 1}


def test_upload_limit_is_enforced_by_backend(client):
    response = client.post("/api/cv/analyze", data={"file": (BytesIO(b'x' * (10 * 1024 * 1024)), "big.docx")})
    assert response.status_code == 413


@pytest.mark.parametrize("route", ["/api/cv/analyze", "/api/cv/normalize", "/api/cv/normalize/docx"])
def test_corrupted_word_is_rejected_without_retaining_source(client, route):
    response = client.post(route, data={"file": (BytesIO(b"not a Word document"), "broken.docx")})
    assert response.status_code == 400
    root = client.application.config["DATA_ROOT"]
    assert not root.exists() or not list(root.iterdir())
