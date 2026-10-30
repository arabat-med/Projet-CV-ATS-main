import os
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor
from docx.text.paragraph import Paragraph
from typing import Dict, List, Optional, Any
from pathlib import Path
import re

# ---------------------------
#   MAPPING DONNÉES -> TEMPLATE
# ---------------------------
def map_extracted_data_to_template(cv_data: Dict) -> Dict:
    """
    Mappe les données extraites aux champs exacts de la template Sopra.
    
    Adapte les données pour correspondre exactement à la structure template:
    - PERIODE_1/2/3: Dates des expériences
    - CLIENT_1/2/3: Entreprises des expériences
    - INTITULE_MISSION_1/2/3: Postes/intitulés des missions
    - FONCTION_1/2/3: Fonctions/rôles dans les missions
    - DESCRIPTION_MISSION_1/2/3: Descriptions détaillées
    - ENV_TECH_1/2/3: Environnement technique utilisé
    
    Args:
        cv_data: Données CV extraites brutes
        
    Returns:
        Dict avec données mappées aux champs template
    """
    mapped = {}
    
    # Traiter les expériences (max 3 pour la template)
    experiences = cv_data.get("experiences", [])[:3]
    
    for i, exp in enumerate(experiences, 1):
        num = str(i)
        
        # PERIODE: Dates
        mapped[f"PERIODE_{num}"] = exp.get("dates") or ""
        
        # CLIENT: Entreprise
        mapped[f"CLIENT_{num}"] = exp.get("entreprise") or ""
        
        # INTITULE_MISSION: Poste/Titre de la mission
        poste = exp.get("poste")
        if poste:
            mapped[f"INTITULE_MISSION_{num}"] = poste
            mapped[f"FONCTION_{num}"] = exp.get("fonction") or ""
        else:
            # Si pas de poste, utiliser la description courte
            desc = exp.get("description", "")
            if desc:
                # Prendre la première ligne ou les 50 premiers caractères
                first_line = desc.split('\n')[0].split('-')[0].strip()
                mapped[f"INTITULE_MISSION_{num}"] = first_line if first_line else "Mission"
                mapped[f"FONCTION_{num}"] = ""
            else:
                mapped[f"INTITULE_MISSION_{num}"] = ""
                mapped[f"FONCTION_{num}"] = ""
        
        # DESCRIPTION_MISSION: Description complète (formattée)
        description = exp.get("description", "")
        if description:
            # Nettoyer la description
            lines = description.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    # Enlever les tirets au début si présents
                    if line.startswith('-'):
                        line = line[1:].strip()
                    clean_lines.append(f"• {line}")
            mapped[f"DESCRIPTION_MISSION_{num}"] = "\n".join(clean_lines) if clean_lines else "Non renseigné"
        else:
            mapped[f"DESCRIPTION_MISSION_{num}"] = ""
        
        # ENV_TECH: Environnement technique (extrait des compétences techniques)
        environnement = exp.get("environnement_technique") or exp.get("environnement") or ""
        mapped[f"ENV_TECH_{num}"] = ", ".join(environnement) if isinstance(environnement, list) else environnement
    
    # Remplir les champs vides (pour les 3 missions)
    for i in range(len(experiences) + 1, 4):
        num = str(i)
        mapped[f"PERIODE_{num}"] = ""
        mapped[f"CLIENT_{num}"] = ""
        mapped[f"INTITULE_MISSION_{num}"] = ""
        mapped[f"FONCTION_{num}"] = ""
        mapped[f"DESCRIPTION_MISSION_{num}"] = ""
        mapped[f"ENV_TECH_{num}"] = ""
    
    return mapped

# ---------------------------
#      HELPERS VISUELS
# ---------------------------

def add_horizontal_line(paragraph, color="7030A0"):
    """Ajoute une ligne horizontale style Sopra (sous le nom du profil)."""
    p = paragraph._p
    pPr = p.get_or_add_pPr()

    pbdr = OxmlElement('w:pBdr')

    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')
    bottom.set(qn('w:color'), color)  # violet Sopra par défaut
    pbdr.append(bottom)

    pPr.append(pbdr)


def set_cell_shading(cell, color):
    """Définit la couleur de fond d'une cellule."""
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), color)
    cell._tc.get_or_add_tcPr().append(shading_elm)

# ---------------------------
#   CLASSIFICATION COMPÉTENCES
# ---------------------------

TECH_KEYWORDS = [
    "python","java","c++","c#","javascript","typescript","sql","docker","kubernetes",
    "aws","azure","gcp","cloud","devops","ci","cd","ci/cd","git","react","angular",
    "vue","node","node.js","django","flask","fastapi","spring","github","gitlab",
    "linux","mongodb","postgresql","mysql","redis","kafka","api","rest","graphql",
    ".net","php","ruby","go","rust","swift","kotlin","scala","html","css","sass"
]

FONC_KEYWORDS = [
    "communication","gestion","travail","team","leadership","équipe","equipe",
    "organisation","planning","collaboration","management","autonomie","analyse",
    "résolution","problèmes","relation","client","négociation","presentation"
]

def classify_competences(lst):
    if not isinstance(lst, list):
        return [], []

    comp_fonct, comp_tech = [], []
    seen_fonct, seen_tech = set(), set()

    for c in lst:
        if not isinstance(c, str):
            continue
        low = c.lower().strip()
        
        if not low or len(low) < 2:
            continue

        if any(k in low for k in TECH_KEYWORDS):
            if low not in seen_tech:
                seen_tech.add(low)
                comp_tech.append(c)
        elif any(k in low for k in FONC_KEYWORDS):
            if low not in seen_fonct:
                seen_fonct.add(low)
                comp_fonct.append(c)
        else:
            if low not in seen_tech:
                seen_tech.add(low)
                comp_tech.append(c)

    return comp_fonct, comp_tech


def group_tech_by_domain(techniques):
    """Regroupe les compétences techniques par domaine (identique au PDF)."""
    if not techniques:
        return {}
    
    domains = {
        "Langages": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin", "scala", "php", "ruby"],
        "Web & Frontend": ["react", "angular", "vue", "html", "css", "bootstrap", "tailwind", "webpack", "vite"],
        "Backend & Frameworks": ["django", "flask", "node", "express", "spring", "laravel", "asp.net", "fastapi"],
        "Bases de données": ["sql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "dynamodb", "cassandra"],
        "DevOps & Cloud": ["docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "jenkins", "gitlab-ci", "github-actions"],
        "Outils & Autres": ["git", "linux", "windows", "macos", "jira", "confluence", "api", "rest", "graphql", "soap"]
    }
    
    result = {}
    seen = set()
    
    for tech in techniques:
        if not tech or not isinstance(tech, str):
            continue
        
        low = tech.lower().strip()
        if low in seen:
            continue
        seen.add(low)
        
        placed = False
        for domain, keywords in domains.items():
            if any(k in low for k in keywords):
                if domain not in result:
                    result[domain] = []
                result[domain].append(tech)
                placed = True
                break
        
        if not placed:
            if "Outils & Autres" not in result:
                result["Outils & Autres"] = []
            result["Outils & Autres"].append(tech)
    
    return result


def format_tech_by_domain(tech_by_domain):
    """Formate les compétences techniques regroupées par domaine pour le DOCX.
    Utilise un format compact sur une ligne pour chaque domaine."""
    if not tech_by_domain:
        return "• Aucune compétence technique"
    
    lines = []
    for domain, techs in tech_by_domain.items():
        # Format compact: Domaine: tech1, tech2, tech3
        techs_str = ", ".join(techs[:4])  # Limiter à 4 par domaine
        lines.append(f"• {domain}: {techs_str}")
    
    return "\n".join(lines) if lines else "• Aucune compétence technique"


def format_tech_by_domain_detailed(tech_by_domain):
    """Formate les compétences techniques avec sous-puces détaillées."""
    if not tech_by_domain:
        return "• Aucune compétence technique"
    
    lines = []
    for domain, techs in tech_by_domain.items():
        lines.append(f"• {domain}:")
        for tech in techs[:4]:  # Limiter à 4 par domaine
            lines.append(f"   - {tech}")
    
    return "\n".join(lines) if lines else "• Aucune compétence technique"

def bullets(lst, fallback="Non renseigné"):
    """
    Génère une liste à puces avec fallback intelligent.
    Gère les listes vides, les None et les valeurs invalides.
    
    Args:
        lst: Liste à formater en bullets
        fallback: Texte par défaut si liste vide
    
    Returns:
        Texte formaté avec puces
    """
    if not lst:
        return f"• {fallback}"
    
    # Filtrer et nettoyer les items
    clean_items = []
    for v in lst:
        if v is None:
            continue
        
        # Convertir en string et nettoyer
        item_str = (" — ".join(str(value) for value in v.values() if value)
                    if isinstance(v, dict) else str(v)).strip()
        
        # Ignorer les items vides
        if not item_str or len(item_str) < 1:
            continue
        
        # Éviter les doublons
        if item_str not in clean_items:
            clean_items.append(item_str)
    
    if not clean_items:
        return f"• {fallback}"
    
    # Formater avec des puces
    return "\n".join(f"• {item}" for item in clean_items)


def format_experiences(exps: List[Dict], style: str = "professional") -> str:
    """
    Formate les expériences avec les données réelles extraites.
    Génère du texte simple (sans markdown) pour meilleure intégration dans DOCX.
    
    Args:
        exps: Liste des expériences structurées
        style: "professional" (détaillé) ou "compact" (résumé)
    """
    if not isinstance(exps, list) or not exps:
        return "Aucune expérience renseignée"

    # Filtrer les expériences vides
    valid_exps = [e for e in exps if isinstance(e, dict) and (e.get("entreprise") or e.get("poste"))]
    
    if not valid_exps:
        return "Aucune expérience renseignée"

    lines = []
    
    # Trier par date (anti-chronologique)
    sorted_exps = sort_experiences_by_date(valid_exps)
    
    for e in sorted_exps:
        # Extraire les données avec des valeurs par défaut
        dates = normalize_date_display(e.get("dates")) if e.get("dates") else ""
        entreprise = (e.get("entreprise") or "").strip()
        poste = (e.get("poste") or "").strip()
        lieu = (e.get("lieu") or "").strip()
        description = (e.get("description") or "").strip()

        if style == "professional":
            # Format professionnel détaillé
            header_parts = []
            if dates:
                header_parts.append(dates)
            if lieu:
                header_parts.append(lieu)
            
            if header_parts:
                lines.append(" – ".join(header_parts))
            
            # Titre: Poste @ Entreprise
            if poste and entreprise:
                lines.append(f"{poste} – {entreprise}")
            elif poste:
                lines.append(f"{poste}")
            elif entreprise:
                lines.append(f"{entreprise}")
            
            # Description formatée avec puces
            if description:
                desc_lines = description.split('\n')
                for line in desc_lines:
                    line = line.strip()
                    if not line:
                        continue
                    # Nettoyer les tirets existants et ajouter puce
                    if line.startswith('-'):
                        line = line[1:].strip()
                    elif line.startswith('•'):
                        line = line[1:].strip()
                    
                    if line:
                        lines.append(f"  • {line}")
            
            environnement = e.get("environnement_technique") or e.get("environnement")
            if environnement:
                if isinstance(environnement, list):
                    environnement = ", ".join(str(item) for item in environnement)
                lines.append("Environnement technique : " + str(environnement))

            # Ligne vide entre expériences
            lines.append("")
        else:
            # Format compact
            title = f"{poste} – {entreprise}" if poste and entreprise else (poste or entreprise or "Expérience")
            if dates:
                title += f" ({dates})"
            lines.append(f"  • {title}")

    return "\n".join(lines).strip() if lines else "Aucune expérience renseignée"


def format_formations(forms: List[Dict], style: str = "professional") -> str:
    """
    Formate les formations avec diplôme si disponible.
    Génère du texte simple (sans markdown) pour meilleure intégration dans DOCX.
    
    Args:
        forms: Liste des formations structurées
        style: "professional" (détaillé) ou "compact" (résumé)
    """
    if not isinstance(forms, list) or not forms:
        return "Aucune formation renseignée"
    
    # Filtrer les formations vides
    valid_forms = [f for f in forms if isinstance(f, dict) and (f.get("diplome") or f.get("etablissement"))]
    
    if not valid_forms:
        return "Aucune formation renseignée"
    
    # Trier par date (anti-chronologique)
    sorted_forms = sort_formations_by_date(valid_forms)
    
    lines = []
    for f in sorted_forms:
        etablissement = (f.get('etablissement') or '').strip()
        diplome = (f.get('diplome') or '').strip()
        dates = normalize_date_display(f.get('dates'))
        lieu = (f.get('lieu') or '').strip()
        
        if style == "professional":
            # Format détaillé
            if diplome:
                lines.append(f"{diplome}")
                details = []
                if etablissement:
                    details.append(etablissement)
                if lieu:
                    details.append(lieu)
                if dates and dates != "Dates non précisées":
                    details.append(f"({dates})")
                
                if details:
                    lines.append(f"  {' – '.join(details)}")
            else:
                # Sans diplôme spécifique
                parts = []
                if etablissement:
                    parts.append(etablissement)
                if lieu:
                    parts.append(lieu)
                if dates and dates != "Dates non précisées":
                    parts.append(f"({dates})")
                
                if parts:
                    lines.append(f"  {' – '.join(parts)}")
            
            # Ligne vide entre formations
            lines.append("")
        else:
            # Format compact
            if diplome:
                title = f"{diplome}"
                if etablissement:
                    title += f" – {etablissement}"
            else:
                title = etablissement if etablissement else "Formation"
            
            if dates and dates != "Dates non précisées":
                title += f" ({dates})"
            
            lines.append(f"  • {title}")
    
    return "\n".join(lines).strip() if lines else "Aucune formation renseignée"


def sort_experiences_by_date(exps: List[Dict]) -> List[Dict]:
    """Trie les expériences par date (anti-chronologique)."""
    def extract_year(exp):
        dates = str(exp.get("dates", ""))
        match = re.search(r'(19|20)\d{2}', dates)
        return int(match.group(0)) if match else 0
    
    return sorted(exps, key=extract_year, reverse=True)


def sort_formations_by_date(forms: List[Dict]) -> List[Dict]:
    """Trie les formations par date (anti-chronologique)."""
    def extract_year(form):
        dates = str(form.get("dates", ""))
        match = re.search(r'(19|20)\d{2}', dates)
        return int(match.group(0)) if match else 0
    
    return sorted(forms, key=extract_year, reverse=True)


def normalize_date_display(date_str: Optional[str]) -> str:
    """Normalise l'affichage des dates."""
    if not date_str:
        return "Dates non précisées"
    
    date_str = str(date_str).strip()
    
    # Normaliser les tirets
    date_str = re.sub(r'\s*[-–—]\s*', ' – ', date_str)
    
    # Normaliser "Présent"
    date_str = re.sub(r'(?i)\b(actuel|actuellement|aujourd\'?hui)\b', 'Présent', date_str)
    
    return date_str


def format_contact(contact):
    """Formate les informations de contact"""
    if not isinstance(contact, dict):
        return ""
    
    lines = []
    if contact.get("email"):
        lines.append(f"Email : {contact['email']}")
    if contact.get("telephone"):
        lines.append(f"Tél : {contact['telephone']}")
    if contact.get("adresse"):
        lines.append(f"Adresse : {contact['adresse']}")
    
    return "\n".join(lines) if lines else "Contact non renseigné"


def detect_template_sections(doc) -> List[str]:
    """
    Détecte les sections disponibles dans la template.
    
    Args:
        doc: Document docx
    
    Returns:
        Liste des sections trouvées (ex: ['experiences', 'formations', 'competences'])
    """
    sections = []
    all_text = ' '.join([p.text.lower() for p in doc.paragraphs])
    all_text += ' '.join([cell.paragraphs[0].text.lower() for table in doc.tables for row in table.rows for cell in row.cells if cell.paragraphs])
    
    # Mots-clés pour identifier les sections
    keywords = {
        'experiences': ['expérience', 'experience', 'emploi', 'professionnel', '{{experiences}}'],
        'formations': ['formation', 'diplôme', 'diplome', 'études', 'etudes', 'école', 'ecole', '{{formations}}'],
        'competences': ['compétence', 'competence', 'skill', 'compétences', 'competences', 'technique', '{{competences}}'],
        'langues': ['langue', 'languages', 'language', '{{langues}}'],
        'certifications': ['certification', 'certifié', '{{certifications}}'],
        'projets': ['projet', 'projects', '{{projets}}'],
        'contact': ['contact', 'email', 'téléphone', 'telephone', '{{contact}}'],
    }
    
    for section, keywords_list in keywords.items():
        if any(kw in all_text for kw in keywords_list):
            sections.append(section)
    
    return sections


# ---------------------------
#   HELPER FOR TEMPLATE REPLACEMENT WITH FORMATTING
# ---------------------------
def replace_text_in_paragraph_with_formatting(paragraph, mapping):
    """
    Remplace les placeholders dans un paragraphe avec formatage intelligent.
    Crée des paragraphes et bullets pour les contenus structurés.
    
    Args:
        paragraph: Paragraphe docx à modifier
        mapping: Dictionnaire {placeholder: valeur}
    """
    full_text = paragraph.text
    replacement_made = False
    
    # Chercher les placeholders
    for key, val in mapping.items():
        if key in full_text:
            val_str = str(val) if val else "Non renseigné"
            
            # Si la valeur contient des retours à la ligne ou des puces, la traiter spécialement
            if '\n' in val_str or val_str.startswith('  •'):
                # Remplacer le placeholder par une version simple
                full_text = full_text.replace(key, "")
                replacement_made = True
                
                # Vider le paragraphe
                for run in paragraph.runs:
                    run.text = ""
                
                # Ajouter le texte structuré
                for line in val_str.split('\n'):
                    if line.strip():
                        # Ajouter le run au paragraphe
                        p = paragraph.add_run(line + '\n') if not paragraph.text else paragraph.insert_paragraph_before(line)
            else:
                full_text = full_text.replace(key, val_str)
                replacement_made = True
    
    if replacement_made and full_text.strip():
        paragraph.text = full_text.strip()


def replace_text_in_paragraph(paragraph, mapping):
    """
    Remplace les placeholders dans un paragraphe en préservant la mise en forme.
    
    Args:
        paragraph: Paragraphe docx à modifier
        mapping: Dictionnaire {placeholder: valeur}
    """
    full_text = paragraph.text
    
    # Chercher les placeholders
    for key, val in mapping.items():
        if key in full_text:
            # Remplacer complètement le texte du paragraphe
            full_text = full_text.replace(key, str(val) if val else "Non renseigné")
    
    # Si du texte a changé, le regénérer avec une mise en forme minimale
    if full_text != paragraph.text:
        paragraph.text = full_text
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def replace_text_in_runs(paragraph, mapping):
    """
    Remplace les placeholders au niveau des runs (éléments de texte) pour préserver la mise en forme.
    Gère aussi les textes multilignes.
    
    Args:
        paragraph: Paragraphe docx à modifier
        mapping: Dictionnaire {placeholder: valeur}
    """
    # Concaténer tous les runs
    full_text = ''.join([run.text for run in paragraph.runs])
    
    # Vérifier s'il y a un remplacement à faire
    for key, val in mapping.items():
        if key in full_text:
            val_str = str(val) if val else "Non renseigné"
            full_text = full_text.replace(key, val_str)
    
    # Mettre à jour le paragraphe en remplaçant complètement le contenu
    # Pour gérer les retours à la ligne correctement
    if full_text != ''.join([run.text for run in paragraph.runs]):
        # Vider les runs existants
        for run in paragraph.runs:
            run._element.getparent().remove(run._element)
        
        # Ajouter le nouveau texte, en gérant les retours à la ligne
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                # Insérer un saut de ligne à la place d'une vraie nouvelle ligne
                paragraph.add_run('\n')
            if line:
                paragraph.add_run(line)


# ---------------------------
#   GENERATE DOCX FINAL
# ---------------------------
def generate_sopra_docx(cv_data, output_path):
    """Remplit le modèle Word ; accepte un chemin ou un flux binaire."""
    template_path = Path(__file__).resolve().parent.parent / "templates/sopra_template.docx"
    doc = Document(template_path)
    contact = cv_data.get("contact") or {}
    comp_fonct, comp_tech = classify_competences(cv_data.get("competences", []))
    formations = format_formations(cv_data.get("formations", []))
    certifications = cv_data.get("certifications", [])
    if certifications:
        formations += "\nCertifications\n" + bullets(certifications)
    mapping = {
        "TITRE_PROFIL": cv_data.get("titre_profil") or "Curriculum vitae",
        "NOM": contact.get("nom") or "", "NOM_PRENOM": contact.get("nom") or "",
        "CONTACT": format_contact(contact),
        "EMAIL": contact.get("email") or "", "TELEPHONE": contact.get("telephone") or "",
        "ADRESSE": contact.get("adresse") or "",
        "COMP_FONCT": bullets(comp_fonct), "COMP_TECH": format_tech_by_domain(group_tech_by_domain(comp_tech)),
        "COMPETENCES": bullets(cv_data.get("competences", [])),
        "EXPERIENCES": format_experiences(cv_data.get("experiences", [])),
        "FORMATIONS": formations, "FORMATIONS_CERTIFICATIONS": formations,
        "LANGUES": bullets(cv_data.get("langues", [])),
        "CERTIFICATIONS": bullets(certifications), "LOISIRS": bullets(cv_data.get("loisirs", [])),
        "PROJETS": bullets(cv_data.get("projets", [])),
        "DISPONIBILITE": cv_data.get("disponibilite") or "",
        **map_extracted_data_to_template(cv_data),
    }

    def paragraphs(container):
        yield from container.paragraphs
        for table in container.tables:
            for row in table.rows:
                for cell in row.cells:
                    yield from paragraphs(cell)

    contact_anchor = None
    for container in [doc, *[part for section in doc.sections for part in (section.header, section.footer)]]:
        for paragraph in list(paragraphs(container)):
            original = paragraph.text
            keys = re.findall(r"\{\{([A-Z0-9_]+)\}\}", original)
            if not keys:
                continue
            if container is doc and "NOM_PRENOM" in keys and mapping.get("NOM_PRENOM"):
                contact_anchor = paragraph
            text = re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: str(mapping.get(m[1]) or ""), original)
            if not any(mapping.get(key) for key in keys) or not text.strip(" -–—|\t\n"):
                paragraph._element.getparent().remove(paragraph._element)
                continue
            text = text.strip(" -–—|\t\n")
            # Le premier run conserve le style du modèle ; Word gère le retour à la ligne.
            runs = paragraph.runs
            if runs:
                runs[0].text = text
                for run in runs[1:]:
                    run.text = ""
            else:
                paragraph.add_run(text)

    if len(cv_data.get("experiences", [])) > 3:
        doc.add_heading("Expériences complémentaires", level=1)
        doc.add_paragraph(format_experiences(cv_data["experiences"][3:]))
    if any(contact.get(key) for key in ("email", "telephone", "adresse")):
        if contact_anchor is not None:
            element = OxmlElement("w:p")
            contact_anchor._p.addnext(element)
            paragraph = Paragraph(element, contact_anchor._parent)
            paragraph.paragraph_format.space_after = Pt(8)
            paragraph.add_run(format_contact(contact)).font.size = Pt(10)
        else:
            doc.add_heading("Contact", level=1)
            doc.add_paragraph(format_contact(contact))
    for key, title in [("projets", "Projets"), ("loisirs", "Loisirs")]:
        if cv_data.get(key):
            doc.add_heading(title, level=1)
            doc.add_paragraph(bullets(cv_data[key]))
    if cv_data.get("disponibilite"):
        doc.add_paragraph("Disponibilité : " + str(cv_data["disponibilite"]))
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    doc.save(output_path)
    return output_path


def generate_cv_documents(cv_data: Dict, output_dir: str, filename: str = None) -> Dict[str, str]:
    """
    Génère les documents CV (DOCX et PDF) à partir des données structurées.
    
    Args:
        cv_data: Données CV structurées (contact, formations, experiences, etc.)
        output_dir: Dossier de sortie
        filename: Nom du fichier (sans extension)
    
    Returns:
        Dict avec les chemins des fichiers générés: {"docx": path, "pdf": path}
    """
    from datetime import datetime
    
    # Créer le dossier si nécessaire
    os.makedirs(output_dir, exist_ok=True)
    
    # Générer le nom de fichier
    if not filename:
        contact = cv_data.get("contact", {}) or {}
        nom = contact.get("nom", "CV")
        # Nettoyer le nom pour le fichier
        nom_clean = re.sub(r'[^\w\s-]', '', nom).strip().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"CV_{nom_clean}_{timestamp}"
    
    docx_path = os.path.join(output_dir, f"{filename}.docx")
    pdf_path = os.path.join(output_dir, f"{filename}.pdf")
    
    result = {"docx": None, "pdf": None}
    
    # Générer le DOCX
    try:
        generate_sopra_docx(cv_data, docx_path)
        result["docx"] = docx_path
        print(f"✓ DOCX généré: {docx_path}")
    except Exception as e:
        print(f"❌ Erreur DOCX: {e}")
        raise
    
    # Générer le PDF
    try:
        from generators.docx_to_pdf import convert_docx_to_pdf
        convert_docx_to_pdf(docx_path, pdf_path)
        result["pdf"] = pdf_path
        print(f"✓ PDF généré: {pdf_path}")
    except ImportError:
        try:
            from docx_to_pdf import convert_docx_to_pdf
            convert_docx_to_pdf(docx_path, pdf_path)
            result["pdf"] = pdf_path
            print(f"✓ PDF généré: {pdf_path}")
        except Exception as e:
            print(f"⚠️ PDF non généré (docx2pdf indisponible): {e}")
    except Exception as e:
        print(f"⚠️ Erreur PDF: {e}")
    
    return result


def validate_cv_data(cv_data: Dict) -> List[str]:
    """
    Valide les données CV avant génération.
    
    Returns:
        Liste des avertissements/erreurs
    """
    warnings = []
    
    # Vérifier les champs obligatoires
    contact = cv_data.get("contact", {})
    if not contact:
        warnings.append("Contact manquant")
    else:
        if not contact.get("nom"):
            warnings.append("Nom manquant dans contact")
        if not contact.get("email"):
            warnings.append("Email manquant dans contact")
    
    # Vérifier les formations
    formations = cv_data.get("formations", [])
    if not formations:
        warnings.append("Aucune formation")
    else:
        for i, f in enumerate(formations):
            if not f.get("etablissement") and not f.get("diplome"):
                warnings.append(f"Formation {i+1}: établissement et diplôme manquants")
    
    # Vérifier les expériences
    experiences = cv_data.get("experiences", [])
    if not experiences:
        warnings.append("Aucune expérience")
    else:
        for i, e in enumerate(experiences):
            if not e.get("entreprise"):
                warnings.append(f"Expérience {i+1}: entreprise manquante")
    
    return warnings


def preview_cv_content(cv_data: Dict) -> str:
    """
    Génère un aperçu texte du contenu CV.
    """
    lines = []
    
    contact = cv_data.get("contact", {})
    lines.append(f"=== {contact.get('nom', 'N/A')} ===")
    lines.append(f"Email: {contact.get('email', 'N/A')}")
    lines.append(f"Tél: {contact.get('telephone', 'N/A')}")
    lines.append("")
    
    lines.append("--- FORMATIONS ---")
    for f in cv_data.get("formations", [])[:3]:
        lines.append(f"  • {f.get('diplome', 'N/A')} - {f.get('etablissement', 'N/A')}")
    
    lines.append("")
    lines.append("--- EXPÉRIENCES ---")
    for e in cv_data.get("experiences", [])[:3]:
        lines.append(f"  • {e.get('poste', 'N/A')} - {e.get('entreprise', 'N/A')}")
    
    lines.append("")
    lines.append("--- COMPÉTENCES ---")
    skills = cv_data.get("competences", [])[:10]
    lines.append(f"  {', '.join(skills) if skills else 'N/A'}")
    
    return "\n".join(lines)
