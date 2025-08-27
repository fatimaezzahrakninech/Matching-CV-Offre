# imports
import spacy
from spacy.matcher import PhraseMatcher

from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor


# init params of skill extractor
nlp = spacy.load("en_core_web_lg")
# init skill extractor
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)




def extract_skills(text):
    """
    Extrait les compétences depuis un texte brut avec SkillNER.
    Retourne une liste d'objets contenant des informations sur chaque compétence.
    """
    annotations = skill_extractor.annotate(text)
    skills = []

    # Parcourir les résultats pour tous les types de matching
    for type_matching, arr_skills in annotations["results"].items():
        for skill in arr_skills:
            # Récupérer le nom de la compétence à partir de l'id
            skill_name = SKILL_DB[skill['skill_id']]['skill_name']
            skill_type = SKILL_DB[skill['skill_id']]['skill_type']
            match_type = type_matching  # Type de correspondance (ex. "full_matches" ou "partial_matches")
            score = skill['score']

            # Créer un objet représentant la compétence
            skill_obj = {
                'skill_name': skill_name,
                'skill_type': skill_type,
                'match_type': match_type,
                'score': score
            }

            skills.append(skill_obj)
    
    return skills
