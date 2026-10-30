"""Normalisation des formats historiques et du JSON d'extraction, sans réécriture."""
from copy import deepcopy
import json
import re
import unicodedata

from docx import Document
from analyser_cv import iter_document_text, extraire_infos_cv


def _unique(items):
    result, seen = [], set()
    for item in items:
        if item is None or item == "":
            continue
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            result.append(deepcopy(item))
    return result


def _list(data, key):
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f'Le champ "{key}" doit être une liste')
    return value


def extract_from_docx(docx_path):
    """Lit les sections d'un ancien DOCX, tableaux inclus, dans l'ordre du document."""
    lines = [line.strip() for block in iter_document_text(Document(docx_path))
             for line in block.splitlines() if line.strip()]
    titles = {
        "competences fonctionnelles": "competences_fonctionnelles",
        "competences techniques": "competences_techniques",
        "competences": "competences_techniques",
        "experience": "experiences", "experiences": "experiences",
        "formation": "formations", "formations": "formations", "diplomes": "formations",
        "langue": "langues", "langues": "langues", "langue(s)": "langues",
        "projets": "projets", "certifications": "certifications", "loisirs": "loisirs",
    }
    sections, current, header = {}, None, []
    for line in lines:
        key = unicodedata.normalize("NFKD", line).encode("ascii", "ignore").decode().lower().strip(" :")
        if key in titles:
            current = titles[key]
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line)
        else:
            header.append(line)
    if not sections:
        raise ValueError("Aucune section reconnue dans le DOCX")
    raw = extraire_infos_cv("\n".join(header))
    sections["contact"] = {
        "nom": header[0] if header else "",
        "email": next(iter(raw["emails"]), ""),
        "telephone": next(iter(raw["telephones"]), ""),
        "adresse": next(iter(raw["adresses"]), ""),
    }
    return sections


def extract_initiales(nom):
    words = str(nom or "").split()
    return (words[0][0] + (words[-1][0] if len(words) > 1 else "")).upper() if words else ""


def extract_contact_info(data):
    contact = data.get("contact", {})
    if not isinstance(contact, dict):
        raise ValueError('Le champ "contact" doit être un objet')
    if any(value is not None and not isinstance(value, str) for value in contact.values()):
        raise ValueError("Les coordonnées doivent être des chaînes de caractères")
    return {key: contact.get(key) or data.get(key) or ""
            for key in ("nom", "email", "telephone", "adresse")}


def group_experiences_into_blocks(lines):
    """Conserve aussi les lignes sans titre daté, auparavant ignorées."""
    blocks, current = [], None
    for line in lines:
        if not isinstance(line, str):
            raise ValueError("Une ligne d'expérience doit être du texte")
        line = line.strip()
        if not line:
            continue
        is_title = bool(re.match(
            r"^(?:(?:janvier|f[eé]vrier|mars|avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|d[eé]cembre)\s+)?\d{4}\b",
            line, re.I))
        if is_title or current is None:
            current = {"titre": line, "missions": [], "environnement": ""}
            blocks.append(current)
        elif line.lower().startswith("environnement technique"):
            current["environnement"] = line.partition(":")[2].strip() or line
        else:
            current["missions"].append(line)
    return blocks


def normalize_old_cv_to_new(cv_data, docx_path=None):
    """Normalise de façon idempotente ; conserve les objets et champs additionnels."""
    if not isinstance(cv_data, dict):
        raise ValueError("Le CV doit être un objet JSON")
    if docx_path is not None:
        cv_data = extract_from_docx(docx_path)
    source = cv_data.get("resultats_spacy", cv_data)
    if not isinstance(source, dict):
        raise ValueError('Le champ "resultats_spacy" doit être un objet')
    if "resultats_spacy" in cv_data:
        source = {**{key: value for key, value in cv_data.items() if key != "resultats_spacy"}, **source}
    for key in ("meta", "header"):
        if key in source and not isinstance(source[key], dict):
            raise ValueError(f'Le champ "{key}" doit être un objet')
    result = deepcopy(source)
    result["contact"] = extract_contact_info(source)
    result["meta"] = {**source.get("meta", {}), "version": "2.0"}
    result["header"] = {
        "titre_document": "CURRICULUM VITAE", "role": source.get("titre_profil") or "",
        "initiales": extract_initiales(result["contact"]["nom"]),
        **source.get("header", {}),
    }
    competences = source.get("competences", [])
    if not isinstance(competences, (list, dict)):
        raise ValueError('Le champ "competences" doit être une liste ou un objet')
    if isinstance(competences, list) and any(not isinstance(item, str) for item in competences):
        raise ValueError("Les compétences doivent être des chaînes de caractères")
    nested = competences if isinstance(competences, dict) else {}
    # Une liste non catégorisée reste dans competences ; aucune catégorie n'est déduite.
    for key, nested_key in [("competences_techniques", "techniques"),
                            ("competences_fonctionnelles", "fonctionnelles")]:
        items = _list(source, key) + _list(nested, nested_key)
        if any(not isinstance(item, str) for item in items):
            raise ValueError("Les compétences doivent être des chaînes de caractères")
        result[key] = _unique(items)
    result["competences"] = _unique(competences) if isinstance(competences, list) else deepcopy(competences)
    experiences, pending = [], []
    for item in _list(source, "experiences"):
        if isinstance(item, dict):
            if "missions" in item and (not isinstance(item["missions"], list)
                                       or any(not isinstance(line, str) for line in item["missions"])):
                raise ValueError("Les missions doivent être une liste de textes")
            experiences.extend(group_experiences_into_blocks(pending))
            pending = []
            experiences.append(deepcopy(item))
        elif isinstance(item, str):
            pending.append(item)
        elif isinstance(item, list) and all(isinstance(line, str) for line in item):
            pending.extend(item)
        else:
            raise ValueError("Format d'expérience non supporté")
    experiences.extend(group_experiences_into_blocks(pending))
    result["experiences"] = _unique(experiences)
    for key in ("formations", "langues", "projets", "certifications", "loisirs"):
        items = _list(source, key)
        if any(not isinstance(item, (str, dict)) for item in items):
            raise ValueError(f'Le champ "{key}" doit contenir des textes ou des objets')
        result[key] = _unique(items)
    return result


def convert_v2_to_old_format(cv_template):
    """Adapte les blocs historiques aux générateurs sans perdre contact ou missions."""
    data = normalize_old_cv_to_new(cv_template)
    result = deepcopy(data)
    comp = data["competences"]
    result["competences"] = _unique(
        (comp if isinstance(comp, list) else [])
        + data["competences_techniques"] + data["competences_fonctionnelles"])
    result["titre_profil"] = data.get("titre_profil") or data["header"].get("role", "")
    result["experiences"] = []
    for exp in data["experiences"]:
        converted = deepcopy(exp)
        if "titre" in exp:
            converted.setdefault("poste", exp["titre"])
            converted.setdefault("description", "\n".join(str(line) for line in exp.get("missions", [])))
            converted.setdefault("environnement_technique", exp.get("environnement", ""))
        if isinstance(converted.get("description"), list):
            converted["description"] = "\n".join(str(line) for line in converted["description"])
        result["experiences"].append(converted)
    result["formations"] = [deepcopy(form) if isinstance(form, dict)
                             else {"diplome": str(form), "dates": "", "etablissement": ""}
                             for form in data["formations"]]
    return result
