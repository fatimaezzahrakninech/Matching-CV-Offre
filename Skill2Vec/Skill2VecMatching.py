from Skill2Vec.utils.convert_to_text import convert_to_text
from Skill2Vec.utils.extract_skills import extract_skills
from gensim.models import Word2Vec
from Skill2Vec.utils.skill2vec_matching import skillset_similarity, get_skill_vector, cosine_similarity
import os


class Skill2VecMatching:
    
    def __init__(self, model_path="https://drive.google.com/uc?export=download&id=1Orr6HYjK6fAIhSM32iRAv5qpnqLwsvoh"):
        """
        Initialise le modèle Word2Vec pré-entrainé.
        """
        self.model = Word2Vec.load(model_path)
        
    def process_input(self, input_data):
        """
        Traite l'entrée (chemin de fichier ou texte brut).
        """
        if isinstance(input_data, str) and os.path.isfile(input_data):
            return convert_to_text(input_data)
        return input_data
    
    def extract_skills_from_text(self, text):
        """
        Extrait les compétences depuis le texte via extract_skills().
        """
        skills = extract_skills(text)
        return self.process_skills(skills)
    
    def process_skills(self, skills):
        """
        Nettoie la liste de compétences (sans doublons, minuscules).
        """
        return list(set(skill["skill_name"].lower() for skill in skills))
    
    def calculate_similarity(self, cv_skills, job_skills):
        """
        Calcule la similarité entre deux listes de compétences.
        """
        return skillset_similarity(cv_skills, job_skills, self.model)
    
    def get_similarity_score(self, cv_input, job_input):
        """
        Calcule le score de similarité entre CV et offre donnés (chemin ou texte).
        """
        cv_text = self.process_input(cv_input)
        job_text = self.process_input(job_input)
        
        cv_skills = self.extract_skills_from_text(cv_text)
        job_skills = self.extract_skills_from_text(job_text)
        
        return self.calculate_similarity(cv_skills, job_skills)
    
    def get_similarity_score_from_skills(self, cv_skills, job_skills):
        """
        Calcule la similarité entre deux listes de compétences déjà extraites.
        """
        scores = []
        for cv_skill in cv_skills:
            vec_cv = get_skill_vector(cv_skill, self.model)
            if vec_cv is None:
                continue
            for job_skill in job_skills:
                vec_job = get_skill_vector(job_skill, self.model)
                if vec_job is None:
                    continue
                sim = cosine_similarity(vec_cv, vec_job)
                scores.append(sim)

        return sum(scores) / len(scores) if scores else 0.0

    def get_vectorized_skills(self, text):
        """
        Retourne les compétences du texte qui sont réellement vectorisées par le modèle.
        """
        tokens = text.lower().split()
        vectorized = [token for token in tokens if token in self.model.wv]
        return [{"skill_name": token} for token in sorted(set(vectorized))]
    
