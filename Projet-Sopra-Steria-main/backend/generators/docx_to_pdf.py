"""Conversion fidèle par un outil externe ; aucun repli textuel silencieux."""
from pathlib import Path
import os
import shutil
import subprocess
from tempfile import TemporaryDirectory


class ConversionUnavailable(RuntimeError):
    """Aucun convertisseur disponible ou capable de produire le PDF."""


def convert_docx_to_pdf(input_docx, output_pdf):
    source, target = Path(input_docx).resolve(), Path(output_pdf).resolve()
    if not source.is_file():
        raise FileNotFoundError("Document DOCX introuvable")
    target.parent.mkdir(parents=True, exist_ok=True)
    candidates = [shutil.which("soffice"), shutil.which("libreoffice")]
    for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
        if os.environ.get(variable):
            candidate = Path(os.environ[variable]) / "LibreOffice/program/soffice.exe"
            if candidate.is_file():
                candidates.append(str(candidate))
    if Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").is_file():
        candidates.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    for binary in dict.fromkeys(item for item in candidates if item):
        # Profil isolé : évite les conflits avec une session LibreOffice ouverte.
        with TemporaryDirectory(prefix="cv-office-") as directory:
            work = Path(directory)
            try:
                result = subprocess.run([
                    binary, f"-env:UserInstallation={(work / 'profile').as_uri()}",
                    "--headless", "--convert-to", "pdf", "--outdir", str(work), str(source),
                ], capture_output=True, timeout=60, check=False)
                converted = work / f"{source.stem}.pdf"
                if result.returncode == 0 and converted.is_file():
                    shutil.copyfile(converted, target)
                    return str(target)
            except (OSError, subprocess.TimeoutExpired):
                continue
    if binary := shutil.which("pandoc"):
        # Une sortie temporaire évite de confondre un ancien fichier avec un succès.
        with TemporaryDirectory(prefix="cv-pandoc-") as directory:
            converted = Path(directory) / "converted.pdf"
            try:
                result = subprocess.run([binary, str(source), "-o", str(converted)],
                                        capture_output=True, timeout=60, check=False)
                if result.returncode == 0 and converted.is_file():
                    shutil.copyfile(converted, target)
                    return str(target)
            except (OSError, subprocess.TimeoutExpired):
                pass
    raise ConversionUnavailable("Aucun convertisseur DOCX vers PDF disponible")
