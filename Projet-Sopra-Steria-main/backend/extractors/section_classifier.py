import re
import sys
import os
from typing import List, Optional, Tuple
import dateparser
from rich.console import Console
from rich.table import Table
import json
from datetime import datetime

# Import adaptatif pour spacy_extractor
try:
    from extractors.spacy_extractor import extraire_entites
except ImportError:
    try:
        from .spacy_extractor import extraire_entites
    except ImportError:
        from spacy_extractor import extraire_entites

console = Console()

# ---------------------
# 0️ Mots-clés enrichis
# ---------------------
FORMATION_KEYWORDS = [
    "université", "universite", "école", "ecole", "diplôme", "diplome",
    "master", "licence", "bachelor", "ingénieur", "ingenieur", "iut",
    "bts", "dut", "bac", "baccalauréat", "doctorat", "phd", "mba",
    "formation", "certificat", "diplômé", "diplome", "cursus", "études"
]
EXPERIENCE_KEYWORDS = [
    "stage", "alternance", "développeur", "developpeur", "full stack",
    "chef de projet", "consultant", "expérience", "experience",
    "ingénieur", "ingenieur", "manager", "stagiaire", "mission",
    "cdi", "cdd", "freelance", "indépendant", "contrat", "poste",
    "employé", "responsable", "directeur", "analyste", "technicien",
    "architecte", "lead", "senior", "junior"
]
STOP_ORG = {
    "assoc", "association", "leadership", "club", "projets", "projet", 
    "volontariat", "bénévolat", "loisirs", "hobbies", "centres", "intérêt",
    # Outils et technologies (PAS des entreprises)
    "plotly", "pandas", "python", "java", "javascript", "html", "css", "sql",
    "git", "github", "jira", "figma", "salesforce", "docker", "kubernetes",
    "react", "angular", "vue", "flask", "django", "spring", "api",
    # Mots génériques
    "microsoft", "outils", "informatique", "outils informatique", "outils microsoft",
    # Sections parasites
    "savoirs", "savoir", "savoir-être", "savoirs-être", "soft skills", "hard skills",
    "compétences", "competences", "compétence", "curiosité", "curiosité culturelle",
    "sens", "détails", "méticuleux", "calme", "autonomie",
    # Pays/Villes (pas des entreprises)
    "allemagne", "france", "espagne", "italie", "portugal", "belgique",
    "paris", "lyon", "marseille", "toulouse", "bordeaux", "boston",
    # Mots de contexte
    "expériences", "experience", "formations", "formation", "langues", "langue"
}

COMPETENCE_KEYWORDS = [
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "docker", "kubernetes", "sql", "mysql", "postgresql", "mongodb",
    "aws", "azure", "gcp", "git", "github", "gitlab", "html", "css",
    "flask", "django", "fastapi", "spring", "linux", "node", "nodejs",
    "api", "rest", "graphql", "ci/cd", "devops", "agile", "scrum",
    "cloud", "communication", "gestion de projet", "leadership", "autonomie",
    "travail en équipe", "résolution de problèmes", "analyse", "c++", "c#",
    ".net", "php", "ruby", "go", "rust", "swift", "kotlin", "scala"
]
LANGUES_KEYWORDS = [
    "français", "francais", "anglais", "espagnol", "allemand", "italien",
    "portugais", "chinois", "mandarin", "japonais", "arabe", "russe",
    "néerlandais", "polonais", "coréen", "hindi"
]

DATE_REGEXES = [
    r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',
    r'\b\d{1,2}[\/\-]\d{4}\b',
    r'\b(?:19|20)\d{2}\b',
    r'\b(?:Janvier|Février|Fevrier|Mars|Avril|Mai|Juin|Juillet|Août|Aout|Septembre|Octobre|Novembre|Décembre)\s+\d{4}\b',
    r'\b(?:\d{4})\s*[-–—]\s*(?:\d{4}|[Pp]résent|[Aa]ctuel(?:lement)?|[Aa]ujourd\'?hui)\b'
]

# ---------------------
# 1️ Extraction de base
# ---------------------
def extraire_competences_langues(texte):
    texte_min = texte.lower()
    competences = []
    langues = []
    
    for m in COMPETENCE_KEYWORDS:
        if re.search(rf"\b{re.escape(m)}\b", texte_min):
            comp = m.title() if len(m) > 3 else m.upper()
            if comp not in competences:
                competences.append(comp)
    
    for m in LANGUES_KEYWORDS:
        if re.search(rf"\b{re.escape(m)}\b", texte_min):
            lang = m.capitalize()
            if lang not in langues:
                langues.append(lang)
    
    return competences, langues


def extract_date_spans(text: str):
    """
    Extrait toutes les dates présentes dans le texte (simples ou plages).
    Renvoie une liste de tuples (brut, start, end, normalisé)
    """
    spans = []
    for rx in DATE_REGEXES:
        for m in re.finditer(rx, text, flags=re.IGNORECASE):
            raw = m.group(0).strip()
            start, end = m.start(), m.end()

            #  1. Détection directe des plages de dates
            if re.match(r"^(?:19|20)\d{2}\s*[-–—]\s*(?:19|20)\d{2}$", raw):
                spans.append((raw, start, end, raw))
                continue

            #  2. Filtrage des faux positifs (code postal, etc.)
            window = text[max(0, start - 8):min(len(text), end + 8)]
            if re.search(r"\b\d{5}\b", window) and re.fullmatch(r"(?:19|20)\d{2}", raw):
                continue

            #  3. Parsing “humain”
            parsed = None
            try:
                dp = dateparser.parse(raw, languages=['fr'])
                if dp:
                    parsed = dp.date().isoformat()

                    #  Filtrer les dates du jour (erreur fréquente de dateparser)
                    if parsed.endswith("-11-12") or parsed.endswith("-11-11"):
                        continue
            except Exception:
                parsed = None

            spans.append((raw, start, end, parsed or raw))

    #  4. Tri + suppression doublons
    spans_sorted = sorted(spans, key=lambda x: x[1])
    unique, seen = [], set()
    for s in spans_sorted:
        if s[1] not in seen:
            unique.append(s)
            seen.add(s[1])
    return unique


def find_org_positions(org: str, text: str) -> List[Tuple[int, int]]:
    return [(m.start(), m.end()) for m in re.finditer(re.escape(org), text, flags=re.IGNORECASE)]


def find_closest_date_by_char(org: str, text: str, date_spans: List[Tuple[str, int, int, str]]) -> Optional[str]:
    org_positions = find_org_positions(org, text)
    if not org_positions:
        return None
    best, best_dist = None, 1200
    for (o_start, o_end) in org_positions:
        for raw, d_start, d_end, parsed in date_spans:
            dist = abs(((o_start + o_end) / 2) - ((d_start + d_end) / 2))
            if dist < best_dist:
                best_dist, best = dist, (parsed or raw)
    return best if best_dist < 1200 else None


# ---------------------
# 2️ Nettoyage
# ---------------------
def nettoyer_nom_organisation(org: str) -> str:
    org = re.sub(r"(?i)(entreprise|projets?|compétences?|competences?|stage|formation)[:\s-]*", "", org)
    org = re.sub(r"\s+", " ", org)
    return org.strip(" :-\n\t")


def is_formation(org_text: str, context_text: str = "") -> bool:
    ol = org_text.lower()
    if any(k in ol for k in FORMATION_KEYWORDS) or any(k in context_text.lower() for k in FORMATION_KEYWORDS):
        return True
    return "univ" in ol or "univers" in ol


def is_valid_school(name: str) -> bool:
    """Vérifie si le nom ressemble à un vrai établissement de formation"""
    name_lower = name.lower().strip()
    
    # Trop court pour être un établissement
    if len(name_lower) < 4:
        return False
    
    # Mots parasites qui ne sont pas des écoles
    INVALID_SCHOOL_WORDS = {
        "culturelle", "culturelle /", "curiosité", "autonomie", "communication",
        "savoir", "savoirs", "être", "faire", "soft", "hard", "skills",
        "sens", "détails", "détail", "méticuleux", "calme", "rigueur",
        # Loisirs / Sports
        "calisthénie", "sport", "musique", "lecture", "voyage", "voyages",
        # Mots techniques
        "serveur", "système", "jeu", "rush", "implémentation", "interaction",
        # Langues (pas des écoles)
        "français", "anglais", "allemand", "espagnol", "italien",
    }
    
    if name_lower in INVALID_SCHOOL_WORDS:
        return False
    
    # Contient un slash ou des caractères suspects
    if "/" in name and "iut" not in name_lower:
        return False
    
    # Un établissement valide contient souvent des mots-clés
    valid_school_keywords = {"école", "ecole", "université", "universite", "iut", 
                             "bts", "lycée", "lycee", "college", "institut",
                             "epita", "epitech", "hec", "essec", "polytechnique",
                             "centrale", "supérieur", "superieur", "nationale"}
    
    if any(kw in name_lower for kw in valid_school_keywords):
        return True
    
    # Accepter les noms propres avec majuscule (ex: "Lycée Hoche")
    words = name.split()
    if len(words) >= 2 and words[0][0].isupper():
        return True
    
    return False


def nettoyer_organisations(entites_org):
    nettoyees = []
    for org in entites_org:
        org_clean = re.sub(r'\s+', ' ', org.strip())
        morceaux = re.split(r'[\-–—](?!\s*(?:19|20)\d{2})', org_clean)
        for part in morceaux:
            part = part.strip(" -–—.,;")
            if len(part) > 2 and part.lower() not in STOP_ORG:
                nettoyees.append(part)
    return list(dict.fromkeys(nettoyees))


# ---------------------
# 3️ Analyse de sections additionnelles
# ---------------------
NIVEAUX = {
    "natif": "C2", "bilingue": "C2", "courant": "C1", "professionnel": "C1",
    "intermédiaire": "B2", "débutant": "A2", "notions": "A1"
}
LANG_LIST = ["français", "francais", "anglais", "espagnol", "allemand", "italien", "portugais", "arabe"]

def parse_section_langues(texte):
    m = re.search(r"(?is)\bLangues?\b\s*[:\-\n]*(.+?)(?:\n\s*(?:Compétences?|Formations?|Expériences?|Certifications?)\b|$)", texte)
    if not m:
        return []
    bloc = m.group(1)
    items = re.split(r"[•\-\u2022,;/\n]+", bloc)
    out = []
    for it in items:
        t = it.strip()
        if not t:
            continue
        low = t.lower()
        if any(l in low for l in LANG_LIST):
            lvl = next((v for k, v in NIVEAUX.items() if re.search(rf"\b{k}\b", low)), None)
            out.append(t if not lvl else f"{t} ({lvl})")
    return list(dict.fromkeys(out))

def parse_section_competences(texte):
    m = re.search(r"(?is)\bCompétences?\b\s*[:\-\n]*(.+?)(?:\n\s*(?:Langues?|Formations?|Expériences?|Certifications?)\b|$)", texte)
    if not m:
        return []
    bloc = m.group(1)
    items = re.split(r"[•\-\u2022,;/\n]+", bloc)
    out = []
    for it in items:
        t = re.sub(r"^[\-\•\d]+\s*", "", it.strip().lower())
        if 2 <= len(t) <= 40 and not re.search(r"\d", t) and not re.search(r"principale", t, re.IGNORECASE):
            out.append(t.capitalize())
    return list(dict.fromkeys(out))

def parse_section_projets(texte):
    matches = re.findall(r"(?:Projets?|Réalisations?)[:\-\n]+([\s\S]+?)(?=\n[A-ZÉÈ]|$)", texte, re.IGNORECASE)
    if not matches:
        return []
    bloc = matches[0]
    items = re.split(r"[•\-\u2022,;\n]+", bloc)
    projets = [i.strip(" .") for i in items if 3 < len(i.strip()) < 80]
    return list(dict.fromkeys(projets))

def parse_section_certifications(texte):
    """
    Extraction amelioree des certifications depuis le texte du CV.
    """
    section_match = re.search(
        r"(?:CERTIFICATIONS?|CERTIF(?:ICATS?)?|ACCREDITATIONS?)\s*[:\-\n]+"
        r"(.+?)(?=\n\s*(?:FORMATIONS?|EXPERIENCES?|COMPETENCES?|LANGUES?|PROJETS?|LOISIRS?|CENTRES?\s+D'INTERET|$))",
        texte, re.IGNORECASE | re.DOTALL
    )
    
    certifs = []
    
    if section_match:
        section_text = section_match.group(1)
        items = re.split(r'[\n\u2022\u2023\u25cf\u25e6•\-]+', section_text)
        for item in items:
            item = item.strip(" ,;:-")
            if len(item) > 3 and len(item) < 100:
                if not re.match(r'^\d{4}$', item):
                    certifs.append(item)
    
    cert_patterns = [
        r"(AWS\s+[A-Za-z\s]+(?:Architect|Developer|Engineer)?)",
        r"(Scrum\s+Master(?:\s+Certified)?)",
        r"(PMP|ITIL|Prince2|TOGAF|COBIT)",
        r"(Cisco\s+(?:CCNA|CCNP|CCIE))",
        r"(Microsoft\s+(?:Azure|Certified)[A-Za-z\s]*)",
        r"(Google\s+(?:Cloud|Certified)[A-Za-z\s]*)",
        r"(Oracle\s+Certified[A-Za-z\s]*)",
        r"(SAFe\s+[A-Za-z\s]+)",
        r"(Certified\s+[A-Za-z\s]+)",
        r"(TOEIC|TOEFL|IELTS|Cambridge)",
    ]
    
    for pattern in cert_patterns:
        for match in re.finditer(pattern, texte, re.IGNORECASE):
            cert = match.group(1).strip()
            if cert and cert not in certifs and len(cert) > 3:
                certifs.append(cert)
    
    seen = set()
    unique_certifs = []
    for c in certifs:
        c_norm = c.lower().strip()
        if c_norm not in seen:
            seen.add(c_norm)
            unique_certifs.append(c)
    
    return unique_certifs

def parse_section_loisirs(texte):
    """
    Extraction des loisirs/centres d'intérêt depuis le texte du CV.
    """
    section_patterns = [
        r"(?:LOISIRS?|CENTRES?\s+D'INTERET|CENTRES?\s+D'INTERETS?|HOBBIES?|PASSIONS?|ACTIVITES?\s+(?:EXTRA[\-\s]?SCOLAIRES?|PERSONNELLES?))\s*[:\-\n]+"
        r"(.+?)(?=\n\s*(?:FORMATIONS?|EXPERIENCES?|COMPETENCES?|LANGUES?|PROJETS?|CERTIFICATIONS?|$))",
    ]
    
    loisirs = []
    
    for pattern in section_patterns:
        section_match = re.search(pattern, texte, re.IGNORECASE | re.DOTALL)
        if section_match:
            section_text = section_match.group(1)
            items = re.split(r'[\n\u2022\u2023\u25cf\u25e6•]+|(?:,\s*(?=[A-Z]))|;\s*', section_text)
            for item in items:
                item = item.strip(" ,-;:")
                item = re.sub(r'^[\-\u2013\u2014]\s*', '', item)
                if len(item) > 2 and len(item) < 50:
                    if not any(kw in item.lower() for kw in ["formation", "experience", "competence", "langue", "projet"]):
                        loisirs.append(item)
            break
    
    seen = set()
    unique_loisirs = []
    for l in loisirs:
        l_norm = l.lower().strip()
        if l_norm not in seen:
            seen.add(l_norm)
            unique_loisirs.append(l)
    
    return unique_loisirs

def parse_disponibilite(texte):
    m = re.search(r"Disponible\s+(?:à partir de|dès)?\s*(.+?)(?:\.|\n|$)", texte, re.IGNORECASE)
    return m.group(1).strip() if m else None


# ---------------------
# Entreprises connues
# ---------------------
KNOWN_COMPANIES = {
    "sopra steria", "capgemini", "accenture", "atos", "cgi", "ibm", "oracle",
    "microsoft", "google", "amazon", "apple", "facebook", "meta", "orange",
    "thales", "airbus", "safran", "dassault", "alstom", "sncf", "edf", "engie",
    "total", "bnp", "société générale", "axa", "carrefour", "renault", "peugeot"
}


def is_valid_company(name: str) -> bool:
    """Vérifie si le nom ressemble à une vraie entreprise"""
    name_lower = name.lower().strip()
    
    if len(name_lower) < 3:
        return False
    
    # Exclure les patterns "Ville Année" comme "Saclay 2013"
    if re.match(r'^[A-Za-zÀ-ÿ]+\s+\d{4}$', name.strip()):
        return False
    
    # Exclure si principalement une date
    if re.match(r'^\d{4}\s*[-–—]?\s*\d{0,4}$', name.strip()):
        return False
    
    # Exclure les villes seules
    CITIES = {"saclay", "paris", "lyon", "marseille", "toulouse", "bordeaux", "nantes",
              "strasbourg", "lille", "rennes", "montpellier", "grenoble", "nice"}
    first_word = name_lower.split()[0] if name_lower.split() else ""
    if first_word in CITIES and len(name_lower.split()) <= 2:
        return False
    
    INVALID_WORDS = {
        "bien", "mal", "détail", "détails", "le", "la", "les", "un", "une", "de", "du",
        "savoirs", "savoir", "curiosité", "autonomie", "calme", "sens", "méticuleux",
        "calisthénie", "sport", "musique", "lecture", "voyage", "voyages",
        "serveur", "système", "jeu", "rush", "module", "composant",
        "expériences", "formations", "compétences", "langues", "projets", "certifications",
        "france", "allemagne", "espagne", "agile", "scrum", "kanban", "devops"
    }
    
    if name_lower in INVALID_WORDS or name_lower in STOP_ORG:
        return False
    
    if name_lower in KNOWN_COMPANIES:
        return True
    
    tech_words = {"python", "java", "javascript", "html", "css", "sql", "git", "docker",
                  "react", "angular", "vue", "flask", "django", "spring", "api"}
    if name_lower in tech_words:
        return False
    
    if name.islower() and len(name.split()) == 1:
        return False
    if len(name.split()) > 5:
        return False
    
    return True


# ---------------------
# Patterns de postes
# ---------------------
POSTE_PATTERNS = [
    r"((?:Développeur|Developpeur|Developer)\s+(?:Full[\s\-]?Stack|Front[\s\-]?End|Back[\s\-]?End|Web|Mobile|Logiciel|Java|Python|\.NET)?)",
    r"((?:Ingénieur|Ingenieur|Engineer)\s+(?:Logiciel|Software|Développement|DevOps|Cloud|Data|IA|ML)?)",
    r"((?:Chef|Responsable|Directeur|Manager)\s+(?:de\s+)?(?:Projet|Produit|Équipe|Technique)?)",
    r"((?:Consultant|Analyste|Architecte)\s+(?:IT|Technique|Fonctionnel|SI)?)",
    r"(Data\s+(?:Scientist|Engineer|Analyst))",
    r"((?:Lead|Senior|Junior)\s+(?:Developer|Développeur|Tech)?)",
    r"(Stagiaire\s+[\w\s]+)",
    r"(Alternant\s+[\w\s]+)"
]


def extract_poste_from_context(context: str) -> Optional[str]:
    """Extrait le poste/titre du contexte"""
    for pattern in POSTE_PATTERNS:
        m = re.search(pattern, context, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
    return None


def extract_titre_profil(texte: str) -> Optional[str]:
    """Extrait le titre/profil du candidat"""
    lines = [l.strip() for l in texte.split('\n') if l.strip()][:20]
    
    for line in lines:
        if len(line) < 5 or len(line) > 80:
            continue
        if re.search(r'[@\d]{6,}', line):
            continue
        
        for pattern in POSTE_PATTERNS:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                return m.group(1).strip().title()
    
    return None


# ---------------------
# Extraction du NOM
# ---------------------
NAME_EXCLUSIONS = {
    "savoirs", "savoir", "soft", "hard", "skills", "compétences", "expériences",
    "formations", "langues", "projets", "certifications", "loisirs", "contact", "profil"
}

def extract_name_from_header(texte: str) -> Optional[str]:
    """Extrait le nom depuis l'en-tête du CV"""
    lines = [l.strip() for l in texte.split('\n') if l.strip()][:15]
    
    for line in lines:
        line_clean = line.strip(" \t\n\r•–—-")
        
        if len(line_clean) < 4 or len(line_clean) > 45:
            continue
        if re.search(r'[@\d]{5,}', line_clean):
            continue
        if re.search(r'\d{5}', line_clean):
            continue
        
        line_lower = line_clean.lower()
        if any(excl in line_lower for excl in NAME_EXCLUSIONS):
            continue
        
        # Pattern Prénom NOM
        if re.match(r'^[A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)*\s+[A-ZÀ-Ÿ]{2,}$', line_clean):
            return line_clean
        
        # Pattern avec majuscules partielles
        words = line_clean.split()
        if 2 <= len(words) <= 4:
            has_upper = any(w.isupper() and len(w) > 1 for w in words)
            has_title = any(w.istitle() for w in words)
            if has_upper or has_title:
                return line_clean
    
    return None


# ---------------------
# Parser de sections
# ---------------------
def extract_section_text(texte: str, section_names: List[str]) -> Optional[str]:
    """Extrait le texte d'une section spécifique"""
    pattern = r'(?:' + '|'.join(section_names) + r')\s*[:\-\n]+(.+?)(?=\n\s*(?:Formations?|Expériences?|Compétences?|Langues?|Projets?|Certifications?|Loisirs?)\s*[:\-\n]|$)'
    match = re.search(pattern, texte, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def parse_formation_section(texte: str) -> List[dict]:
    """Parse la section Formations du CV"""
    formations = []
    
    section_text = extract_section_text(texte, ["FORMATION", "FORMATIONS", "ÉTUDES", "EDUCATION", "CURSUS"])
    if not section_text:
        return formations
    
    # Pattern: Date | École | Diplôme
    lines = section_text.split('\n')
    current = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Chercher une date
        date_match = re.search(r'(\d{4})\s*[-–—]\s*(\d{4}|[Pp]résent|[Aa]ctuel)', line)
        
        if date_match:
            if current:
                formations.append(current)
            
            dates = date_match.group(0)
            rest = line.replace(dates, '').strip(' |:-')
            
            # Chercher diplôme
            diplome_match = re.search(r'(Master|Licence|Bachelor|DUT|BTS|Ingénieur|Doctorat|MBA|BAC)[\w\s]*', rest, re.IGNORECASE)
            diplome = diplome_match.group(0).strip() if diplome_match else None
            
            # Chercher établissement
            etab = rest.replace(diplome or '', '').strip(' |:-') if diplome else rest
            
            current = {
                "etablissement": etab if etab else None,
                "dates": dates,
                "diplome": diplome
            }
        elif current:
            # Ligne de continuation
            if not current.get("diplome"):
                diplome_match = re.search(r'(Master|Licence|Bachelor|DUT|BTS|Ingénieur|Doctorat|MBA)[\w\s]*', line, re.IGNORECASE)
                if diplome_match:
                    current["diplome"] = diplome_match.group(0).strip()
    
    if current:
        formations.append(current)
    
    return formations


def parse_experience_section(texte: str) -> List[dict]:
    """Parse la section Expériences du CV"""
    experiences = []
    
    section_text = extract_section_text(texte, ["EXPÉRIENCE", "EXPERIENCE", "EXPÉRIENCES", "EXPERIENCES"])
    if not section_text:
        return experiences
    
    lines = section_text.split('\n')
    current = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Chercher une date
        date_match = re.search(r'(\d{4})\s*[-–—]\s*(\d{4}|[Pp]résent|[Aa]ctuel)', line)
        
        if date_match:
            if current and current.get("entreprise"):
                experiences.append(current)
            
            dates = date_match.group(0)
            rest = line.replace(dates, '').strip(' |:-')
            
            # Chercher poste
            poste = extract_poste_from_context(rest)
            
            # Chercher entreprise
            entreprise = rest.replace(poste or '', '').strip(' |:-') if poste else rest
            entreprise = re.sub(r'^[\|:\-\s]+', '', entreprise).strip()
            
            current = {
                "entreprise": entreprise if entreprise and is_valid_company(entreprise) else None,
                "poste": poste,
                "dates": dates,
                "description": ""
            }
        elif current:
            if line.startswith('-') or line.startswith('•'):
                desc = line.lstrip('-•').strip()
                if current["description"]:
                    current["description"] += "\n- " + desc
                else:
                    current["description"] = "- " + desc
    
    if current and current.get("entreprise"):
        experiences.append(current)
    
    return experiences


def classifier_formations_experiences(texte: str, entites: dict, dates: List[str]):
    """Classifie les organisations en formations et expériences"""
    formations, experiences = [], []
    date_spans = extract_date_spans(texte)
    
    # PRIORITÉ 1: Parser les sections directement
    parsed_formations = parse_formation_section(texte)
    if parsed_formations:
        for f in parsed_formations:
            if f.get("etablissement") or f.get("diplome"):
                formations.append(f)
    
    parsed_experiences = parse_experience_section(texte)
    if parsed_experiences:
        for e in parsed_experiences:
            if e.get("entreprise"):
                experiences.append(e)
    
    # FALLBACK: Utiliser les entités NER si les parsers n'ont rien trouvé
    if not formations:
        for ecole in entites.get("ecoles", []):
            ecole_clean = nettoyer_nom_organisation(ecole)
            if ecole_clean and is_valid_school(ecole_clean):
                date = find_closest_date_by_char(ecole_clean, texte, date_spans)
                formations.append({
                    "etablissement": ecole_clean,
                    "dates": date,
                    "diplome": None
                })
    
    if not experiences:
        for entreprise in entites.get("entreprises", []):
            entreprise_clean = nettoyer_nom_organisation(entreprise)
            if entreprise_clean and is_valid_company(entreprise_clean):
                date = find_closest_date_by_char(entreprise_clean, texte, date_spans)
                poste = extract_poste_from_context(texte)
                experiences.append({
                    "entreprise": entreprise_clean,
                    "poste": poste,
                    "dates": date,
                    "description": None
                })
    
    # Déduplication
    def dedupe(lst, key):
        seen = {}
        for item in lst:
            k = (item.get(key) or "").lower()
            if k and k not in seen:
                seen[k] = item
        return list(seen.values())
    
    return dedupe(formations, "etablissement"), dedupe(experiences, "entreprise")


# ---------------------
# Construction JSON finale
# ---------------------
def build_structured_json(emails, telephones, adresses, dates, texte_cv):
    """Construit le JSON structuré à partir des données extraites"""
    entites = extraire_entites(texte_cv)
    entites["organisations"] = nettoyer_organisations(entites.get("organisations", []))
    
    # Nom
    nom = extract_name_from_header(texte_cv)
    if not nom and entites.get("noms"):
        nom = entites["noms"][0] if entites["noms"] else None
    
    # Titre profil
    titre_profil = extract_titre_profil(texte_cv)
    
    # Contact
    contact = {
        "nom": nom,
        "email": emails[0] if emails else None,
        "telephone": telephones[0] if telephones else None,
        "adresse": adresses[0] if adresses else None
    }
    
    # Formations et Expériences
    formations, experiences = classifier_formations_experiences(texte_cv, entites, dates)
    
    # Compétences et Langues
    comp_kw, lang_kw = extraire_competences_langues(texte_cv)
    comp_sec = parse_section_competences(texte_cv)
    lang_sec = parse_section_langues(texte_cv)
    
    # Autres sections
    projets = parse_section_projets(texte_cv)
    certifs = parse_section_certifications(texte_cv)
    loisirs = parse_section_loisirs(texte_cv)
    dispo = parse_disponibilite(texte_cv)
    
    # Fusion et nettoyage
    competences = list(set(comp_kw + comp_sec + entites.get("competences", [])))
    langues = list(set(lang_kw + lang_sec + entites.get("langues", [])))
    
    # JSON final
    json_final = {
        "contact": contact,
        "titre_profil": titre_profil,
        "formations": formations if formations else [],
        "experiences": experiences if experiences else [],
        "competences": sorted(set(competences)) if competences else [],
        "langues": sorted(set(langues)) if langues else [],
        "projets": projets if projets else [],
        "certifications": certifs if certifs else [],
        "loisirs": loisirs if loisirs else [],
        "disponibilite": dispo,
        "dates": dates if dates else []
    }
    
    return json_final


def afficher_json_rich(data: dict, titre: str = "Données Structurées"):
    """Affiche le JSON formaté avec Rich"""
    table = Table(title=titre, show_header=True, header_style="bold cyan")
    table.add_column("Champ", style="bold")
    table.add_column("Valeur")
    
    for key, value in data.items():
        if isinstance(value, dict):
            val_str = json.dumps(value, ensure_ascii=False, indent=2)
        elif isinstance(value, list):
            val_str = "\n".join([str(v) for v in value]) if value else "[]"
        else:
            val_str = str(value) if value else "N/A"
        table.add_row(key, val_str)
    
    console.print(table)


if __name__ == "__main__":
    # Test rapide
    test_text = """
    Jean DUPONT
    Développeur Full Stack
    
    EXPÉRIENCES
    2020 – Présent | Sopra Steria | Lead Développeur
    - Développement d'applications web
    
    FORMATIONS
    2015 – 2017 | École Centrale Paris | Master Informatique
    
    COMPÉTENCES
    Python, Java, React, Docker
    
    LANGUES
    Français (natif), Anglais (courant)
    """
    
    result = build_structured_json(
        emails=["jean.dupont@email.com"],
        telephones=["06 12 34 56 78"],
        adresses=["Paris"],
        dates=["2020 – Présent", "2015 – 2017"],
        texte_cv=test_text
    )
    
    afficher_json_rich(result, "Test Extraction CV")
