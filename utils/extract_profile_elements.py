from datetime import datetime
import re
from typing import List, Dict

# === Chargement du dictionnaire depuis skills_list.txt ===
def load_skill_dictionary(path: str = "utils/skills_list.txt") -> List[str]:
    all_skills = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            terms = line.strip().split()
            all_skills.extend(terms)
    return all_skills

# === Nettoyage générique des compétences (sans altérer la casse) ===
def clean_terms(terms: List[str]) -> List[str]:
    cleaned = set()
    for term in terms:
        term = term.strip()
        if len(term) < 2 or len(term.split()) > 6:
            continue
        if re.search(r"\b(19|20)\d{2}\b", term): continue
        if "@" in term or re.search(r"\b(gmail|yahoo|hotmail)\b", term): continue
        cleaned.add(term)
    return sorted(cleaned)

# === Formatage lisible des compétences ===
def format_skill_display(skills: List[str]) -> List[str]:
    return [skill.replace("_", " ") for skill in skills]

# === Nettoyage des déterminants élidés (prétraitement du texte) ===
def remove_elided_determiners(text: str) -> str:
    # Supprime les déterminants élidés comme "l’optimisation", "d’analyse", etc.
    text = re.sub(r"\b[ldLD][’']\s*", "", text)
    return text

def extract_formation(text: str) -> Dict:
    formation = {"intitulé": "Non précisé", "état": "Non précisé"}
    
    # === Détection du diplôme avec priorisation typologique
    diplome_patterns = [
        r"(phd|doctorat)",
        r"(master spécialisé|master|bac\+5)",
        r"(licence professionnelle|licence|bachelor|bac\+3)",
        r"(bts|dut|technicien spécialisé|bac\+2)",
        r"(dipl[oô]me d[’']ing[ée]nieur|engineering degree)"
    ]
    
    for pattern in diplome_patterns:
        match_title = re.search(pattern, text, re.IGNORECASE)
        if match_title:
            formation["intitulé"] = match_title.group(1).lower()
            break  # Priorité au premier match typologique

    # === Détection explicite de l’obtention
    current_year = datetime.now().year
    current_month = datetime.now().month
    obtention_match = re.search(r"(obtenu en|obtention en|graduated in|obtained in)\s*(\d{4})", text, re.IGNORECASE)
    if obtention_match:
        obtention_year = int(obtention_match.group(2))
        if obtention_year < current_year or (obtention_year == current_year and current_month >= 6):
            formation["état"] = "Terminé"
            return formation

    # === Extraction des dates de formation
    date_match = re.search(r"(\d{4})\s*[–\-]\s*(\d{4})", text)
    if date_match:
        start_year = int(date_match.group(1))
        end_year = int(date_match.group(2))
        if end_year < current_year or (end_year == current_year and current_month >= 6):
            formation["état"] = "Terminé"
        elif start_year <= current_year <= end_year:
            formation["état"] = "En cours"
        else:
            formation["état"] = "À venir"
    else:
        # === Fallback sur les mots-clés
        if re.search(r"(en cours|actuellement|ongoing|present|now)", text, re.IGNORECASE):
            formation["état"] = "En cours"
        elif formation["intitulé"] != "Non précisé":
            formation["état"] = "Terminé"  # Supposition par défaut
        else:
            formation["état"] = "Non précisé"

    return formation

# === Compétences techniques ===
def extract_technical_terms(text: str, skill_dict_path: str = "utils/skills_list.txt") -> List[str]:
    known_skills = load_skill_dictionary(skill_dict_path)
    found_skills = set()

    # Nettoyage des déterminants élidés
    text = remove_elided_determiners(text)

    # Normalisation
    normalized_text = re.sub(r"[\n\r\t]", " ", text)
    normalized_text = re.sub(r"[^\w\s/]", " ", normalized_text)
    normalized_text = re.sub(r"\s+", " ", normalized_text).lower()

    # Expressions à ignorer (phrases d’annonce, pas des compétences)
    ignore_contexts = [
        r"\bwe are hiring\b",
        r"\bjoin our team\b",
        r"\bapply now\b",
        r"\bwe are recruiting\b",
        r"\blooking for\b",
        r"\bjob opening\b",
        r"\bvacancy\b"
    ]

    for raw_skill in known_skills:
        skill_phrase = raw_skill.replace("_", " ").lower()

        # Cas particulier : "R"
        if raw_skill.lower() == "r":
            if not re.search(r"\b(rstudio|tidyverse|ggplot2|r programming|r langage|langage r)\b", normalized_text):
                continue

        # Cas particulier : "C"
        if raw_skill.lower() == "c":
            if not re.search(r"\b(c programming|embedded systems|c langage|langage c|gcc|clang|pointers|memory management)\b", normalized_text):
                continue

        # Vérification du contexte d’annonce
        if raw_skill.lower() in ["hiring", "recruiting", "job", "vacancy"]:
            if any(re.search(ctx, normalized_text) for ctx in ignore_contexts):
                continue  # Ignore si le mot apparaît dans un contexte d’annonce

        # Matching direct
        pattern = rf"\b{re.escape(skill_phrase)}\b"
        if re.search(pattern, normalized_text):
            found_skills.add(raw_skill)

        # Matching combiné pour les compétences composées
        if "/" in skill_phrase:
            subskills = skill_phrase.split("/")
            if all(re.search(rf"\b{sub}\b", normalized_text) for sub in subskills):
                found_skills.add(raw_skill)

    return sorted(format_skill_display(list(found_skills)))

# === Normalisation des soft skills ===
def normalize_soft_skills(raw_skills: List[str]) -> List[str]:
    mapping = {
        # Regroupements FR/EN avec variantes typographiques
        "team coordination": "coordination d’équipe",
        "coordination d’équipe": "coordination d’équipe",
        "client relationship": "sens du service",
        "relation client": "sens du service",
        "problem-solving": "résolution de problèmes",
        "résolution de problèmes": "résolution de problèmes",
        "resource management": "gestion des priorités",
        "gestion des priorités": "gestion des priorités",
        "teamwork": "travail en équipe",
        "travail en équipe": "esprit d'équipe",
        "travailler en équipe": "esprit d'équipe",
        "active listening": "écoute active",
        "écoute active": "écoute active",
        "time management": "gestion du temps",
        "gestion du temps": "gestion du temps",
        "analytical thinking": "esprit d’analyse",
        "esprit analytique": "esprit d’analyse",
        "esprit d’analyse": "esprit d’analyse",
        "esprit d'analyse": "esprit d’analyse", 
        "initiative": "prise d’initiative",
        "prise d’initiative": "prise d’initiative",
        "attention to detail": "sens du détail",
        "sens du détail": "sens du détail",
        "autonomy": "autonomie",
        "analytical mindset": "esprit d’analyse",
        "curious": "curiosité",
        "curiosity" : "curiosité",
        "curiosité": "curiosité",
        "passionate": "passionné(e)",
        "passion": "passion",
        "passionné": "passionné",
        "passionnée": "passionnée",
        "curiosité": "curieux",
        "curiosité": "curieuse",
        "leadership": "leadership",
        "créativité": "créativité",
        "creativity": "créativité",
        "créativité" : "créative",
        "créativité" : "creative",
        "créativité" : "créatif",
        "empathie": "empathie",
        "empathy": "empathie",
        "adaptabilité": "adaptabilité",
        "adaptabilité":"rapidité d’adaptation",
        "adaptability": "adaptabilité",
        "rigueur": "rigueur",
        "rigor" : "rigueur",
        "rigoureuse": "rigueur",
        "rigoureux": "rigueur",
        "sens du résultat": "sens du résultat",
        "réactivité" : "réactivité",
        "responsiveness" : "réactivité",
        "reactivity" : "réactivité",
        "résistance au stress" : "résistance au stress",
        "stress tolerance" : "résistance au stress",
        "stress resilience" : "résistance au stress",
        "ability to handle stress" : "résistance au stress",
        "working under pressure" : "travail sous pression",
        "work under pressure" : "travail sous pression",
        "travail sous pression" : "travail sous pression",
        "sens de l’organisation" : "sens de l’organisation",
        "organizational skills" : "sens de l’organisation",
        "sense of organization" : "sens de l’organisation",
        "strong organizational skills" : "sens de l’organisation",
        "organisation": "organisation",
        "organisation":" organisée",
        "organisation":" organisé",
        "organization" : "organisation",
        "organizational ability" : "organisation",
        "organizational skills" : "organisation",
        "amélioration continue" : "amélioration continue",
        "continuous improvement" : "amélioration continue",
        "learning new technologies": "apprentissage des nouvelles technologies",
        "apprentissage des nouvelles technologies": "apprentissage des nouvelles technologies",
        "learn new technologies": "apprentissage des nouvelles technologies",
        "technological curiosity": "apprentissage des nouvelles technologies",
        "service orientation" : "orientation service",
        "orientation service" : "orientation service",
        "ability to manage priorities" : "gestion des priorités",
        "esprit analytique" : "esprit analytique",
        "forte discipline " : "forte discipline ",
        "strong discipline" : "forte discipline ",
        "high level of discipline" : "forte discipline ",
        "discipline" : "discipline",
        "prise de parole en public" : "prise de parole en public",
        "public speaking" : "prise de parole en public",
        "compétences en présentation" : "compétences en présentation",
        "presentation skills" : "compétences en présentation",
        "ability to present" : "compétences en présentation",
        "communication interfonctionnelle" : "communication interfonctionnelle",
        "cross-functional communication" : "communication interfonctionnelle",
        "interdepartmental communication" : "communication interfonctionnelle",
        "esprit critique" : "esprit critique",
        "critical thinking" : "esprit critique",
        "orientation client" : "orientation client",
        "customer orientation" : "orientation client",
        "esprit d’équipe" : "esprit d’équipe",
        "esprit d'équipe" : "esprit d'équipe",
        "team spirit": "esprit d'équipe",
        "team mindset" : "esprit d'équipe",
        "collaborative attitude" : "esprit d'équipe",
        "cross-functional collaboration" : "travail en équipe",
        "collaboration" : "travail en équipe",
        "planning": "gestion du temps",
        "inventory": "gestion des priorités",
        "wise": "esprit critique",
        "wisdom": "esprit critique",
        "judgment": "esprit critique",
        "discernment": "esprit critique",
        "flexibility": "flexibilité",
        "flexibilité": "flexibilité",
        "adaptabilité professionnelle": "flexibilité",
        "adaptation rapide": "flexibilité",
        "sense of responsibility": "sens des responsabilités",
        "responsibility": "sens des responsabilités",
        "sens de responsabilité": "sens des responsabilités",
        "sens de responsabilité" : "sens de responsabilité",
        "responsable": "sens des responsabilités",
        "disciplinary rigor": "rigueur disciplinaire",
        "rigueur disciplinaire": "rigueur disciplinaire",
        "discipline professionnelle": "rigueur disciplinaire",
        "welcoming attitude": "accueil",
        "accueil": "accueil",
        "reception skills": "accueil",
        "hospitality": "accueil",
        "social climate awareness": "gestion du climat social",
        "gestion du climat social": "gestion du climat social",
        "employee relations sensitivity": "gestion du climat social",
        "conflict management": "gestion des conflits",
        "gestion des conflits": "gestion des conflits",
        "conflict resolution": "gestion des conflits",
        "emotional intelligence": "intelligence émotionnelle",
        "intelligence émotionnelle": "intelligence émotionnelle",
        "emotional awareness": "intelligence émotionnelle",
        "professional ethics": "éthique professionnelle",
        "éthique professionnelle": "éthique professionnelle",
        "work ethics": "éthique professionnelle",
        "precision": "précision",
        "accuracy": "précision",
        "attention to accuracy": "précision",
        "précision": "précision",
        "autonome": "autonomie",
        "flexible": "flexibilité",
        "Sens de l’organisation": "organisation",
        "capacité d’adaptation": "adaptation",
        "capacité d'adaptation": "adaptation",
        "capacité de prioriser": "gestion des priorités",
        "priority management": "gestion des priorités",
        "multitâche" : "multitâche",
        "sens du service" : "sens du service",
        "service mindedness": "sens du service",
        "gestion du stress": "gestion du stress",
        "stress management" : "gestion du stress",
        "ponctualité" : "ponctualité",
        "ponctuelle":"ponctualité",
        "ponctuel":"ponctualité",
        "punctuality" :"ponctualité",
        "punctual": "ponctualité",
        "service orientation" : "sens du service",
        "confiance en soi": "confiance en soi",
        "self-confidence": "confiance en soi",
        "self-assurance": "confiance en soi",
        "confidence": "confiance en soi",
        "sérieuse": "sérieuse",
        "sérieux": "sérieux",
        "reliable": "sérieu(x/se)",
        "serious": "sérieu(x/se)",
        "conscientious": "sérieu(x/se)",
        "diligent" : "sérieu(x/se)",
        "adaptable": "adaptabilité",
        "dynamisme": "dynamisme",
        "dynamique": "dynamisme",
        "interpersonal skills": "relationnel",
        "interpersonal": "relationnel",
        "communication aptitude": "relationnel",
        "relationnel": "relationnel",
        "reliability": "fiabilité",
        "trustworthiness": "fiabilité",
        "fiabilité": "fiabilité",
        "professionalism": "professionnalisme",
        "workplace ethics": "professionnalisme",
        "professionnalisme": "professionnalisme",
        "polyvalence": "polyvalence",
        "polyvalence": "polyvalente",
        "polyvalence":"polyvalent"
    }
    normalized = set()
    for skill in raw_skills:
        key = skill.lower()
        value = mapping.get(key, key)
        normalized.add(value)
    return sorted(normalized)


# === Soft skills enrichies (FR + EN) ===
def extract_soft_skills(text: str) -> List[str]:
    soft_keywords = [
        "communication", "travail en équipe", "autonomie", "autonome","adaptabilité", "écoute active", "créative", "créatif", "réactivité",
        "rigueur", "esprit analytique", "esprit d’analyse", "esprit d'analyse", "curiosité", "sens du résultat", "gestion du temps",
        "leadership", "résolution de problèmes", "créativité", "empathie", "prise d’initiative", "résistance au stress", " organisée"
        "coordination d’équipe", "gestion des priorités", "sens du service", "relation client", "sens de l’organisation", " organisé"
        "sens du détail", "curiosité", "curieux", "curieuse","passion", "passionné", "passionnée", "organisation", "amélioration continue",
        "apprentissage des nouvelles technologies", "orientation service", "travail sous pression", "esprit critique", "orientation client",
        "forte discipline ", "discipline", "prise de parole en public", "compétences en présentation", "communication interfonctionnelle",
        "esprit d’équipe", "esprit d'équipe", "flexibilité", "flexibility", "adaptabilité professionnelle", "adaptation rapide",
        "capacité d’adaptation", "capacité d'adaptation","capacité de prioriser", "multitâche", "sens du service","gestion du stress",
        "sens des responsabilités", "sens de responsabilité","sense of responsibility", "responsibility", "responsable","rigueur disciplinaire", 
        " flexible", "ponctuelle", "ponctuel", "confiance en soi", "sérieuse", "sérieux", "adaptable", "dynamisme", "dynamique",
        "rigoureuse", "rigoureux","interpersonal skills","relationnel","interpersonal","communication aptitude","reliability",
        "fiabilité","trustworthiness","professionalism", "professionnalisme","workplace ethics", "travailler en équipe",
        "rapidité d’adaptation","polyvalence", "polyvalente", "polyvalent",
        "disciplinary rigor", "discipline professionnelle","accueil", "welcoming attitude", "reception skills", "hospitality",
        "gestion du climat social", "social climate awareness", "employee relations sensitivity","gestion des conflits", "ponctualité",
        "conflict management", "conflict resolution","intelligence émotionnelle", "emotional intelligence", "emotional awareness",
        "éthique professionnelle", "professional ethics", "work ethics","précision", "precision", "accuracy", "attention to accuracy"
        "attention to detail", "teamwork", "team spirit","adaptability", "active listening", "time management", "problem solving", 
        "responsiveness","reactivity","creativity", "initiative", "empathy", "analytical thinking", "team coordination", "creative", 
        "stress tolerance","ability to handle stress","working under pressure","client relationship", "resource management", "autonomy", 
        "analytical mindset", "curious", "passionate", "organizational skills", "sense of organization", "strong organizational skills", 
        "organization","organizational ability", "organizational skills", "continuous improvement", "learning new technologies", 
        "learn new technologies","technological curiosity", "rigor", "stress resilience", "service orientation", "curiosity", 
        "ability to manage priorities","work under pressure", "strong discipline", "high level of discipline", "public speaking", 
        "presentation skills","ability to present", "cross-functional communication", "interdepartmental communication", "punctuality",
        "critical thinking","customer orientation", "team mindset", "collaborative attitude", "cross-functional collaboration", 
        "collaboration","planning", "inventory", "wise", "wisdom", "judgment", "discernment", "service mindedness", "stress management",
        "priority management", "service orientation", "punctual", "self-confidence", "self-assurance", "confidence", "reliable",
        "serious", "conscientious", "diligent"
    ]

    # Nettoyage typographique des apostrophes
    text_clean = text.replace("’", "'").replace("‘", "'").replace("`", "'").lower()
    text_clean = re.sub(r"\s+", " ", text_clean)

    raw = set()

    # 1. Extraction via segments déclenchés
    triggers = ["compétences en", "maîtrise de", "expérience en"]
    for trigger in triggers:
        matches = re.findall(rf"{trigger}\s+([^.:\n]+)", text_clean)
        for segment in matches:
            parts = re.split(r"[,\n;]| et | ainsi que ", segment)
            for part in parts:
                part = part.strip()
                for kw in soft_keywords:
                    if re.search(rf"\b{re.escape(kw)}\b", part):
                        raw.add(kw)

    # 2. Match direct dans tout le texte
    for kw in soft_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text_clean):
            raw.add(kw)

    return normalize_soft_skills(list(raw))

# === Normalisation des langues ===
def extract_languages(text: str) -> List[str]:
    # Liste des langues connues
    known_langs = {
        "français": ["français", "french"],
        "anglais": ["anglais", "english"],
        "arabe": ["arabe", "arabic", "arab"],
        "amazigh": ["amazigh"],
        "espagnol": ["espagnol", "spanish", "espagne"],
        "allemand": ["allemand", "german"],
        "turc": ["turc", "turkish"],
        "italien": ["italien", "italian"],
        "portugais": ["portugais", "portuguese"],
        "néerlandais": ["néerlandais", "dutch"]
    }

    found = set()
    # Nettoyage du texte
    clean_text = text.lower().replace('\n', ' ').replace('\r', ' ')
    
    for lang_key, variants in known_langs.items():
        for variant in variants:
            # Match souple : langue suivie de : ou niveau
            pattern = rf"{variant}\s*[:\-]?\s*(native|fluent|intermediate|courant|débutant)?"
            if re.search(pattern, clean_text, re.IGNORECASE):
                found.add(lang_key)
                break  # Une fois trouvé, inutile de tester les autres variantes

    return sorted(found)

# === Langues enrichies ===
def normalize_languages(raw_langs: List[str]) -> List[str]:
    mapping = {
        "french": "français", "français": "français",
        "english": "anglais", "anglais": "anglais",
        "arabic": "arabe", "arabe": "arabe", "arab": "arabe",
        "amazigh": "amazigh",
        "spanish": "espagnol", "espagnol": "espagnol", "espagne": "espagnol",
        "german": "allemand", "allemand": "allemand",
        "turkish": "turc", "turc": "turc",
        "italian": "italien", "italien": "italien",
        "portuguese": "portugais", "portugais": "portugais",
        "dutch": "néerlandais", "néerlandais": "néerlandais"
    }

    normalized = set()
    for lang in raw_langs:
        lang_clean = lang.strip().lower()
        normalized.add(mapping.get(lang_clean, lang_clean))
    return sorted(normalized)


# === Structuration complète ===
def extract_structured_elements(text: str, skill_dict_path: str = "utils/skills_list.txt") -> Dict:
    is_offer = "job title" in text.lower() or "requirements" in text.lower() or "exigences" in text.lower()
    return {
        "formation": extract_formation(text),
        "competences": extract_technical_terms(text, skill_dict_path),
        "soft_skills": extract_soft_skills(text),
        "languages": extract_languages(text)
    }
