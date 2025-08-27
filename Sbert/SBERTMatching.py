from sentence_transformers import SentenceTransformer, util
import torch
import os
from Sbert.utils.convert_to_text import convert_to_text




class SBERTMatching:
    """
    Classe pour effectuer un matching sémantique entre deux documents
    (CV et offre d’emploi) à l’aide de SBERT (Sentence-BERT).
    """

    def __init__(self, model_path='output/sbert_regression_finetuned'):
        """
        Initialise le modèle SBERT à partir du chemin fourni.

        Args:
        - model_path (str): Chemin vers le modèle Sentence-BERT fine-tuné.
        """
        self.model = SentenceTransformer(model_path)

    def process_input(self, input_data):
        """
        Traite l'entrée : détecte si c'est un chemin de fichier (.txt, .pdf) ou un texte brut.
        
        Args:
        - input_data (str): Chemin vers un fichier ou texte brut.
        
        Returns:
        - str: Contenu texte extrait ou texte brut.
        """
        if isinstance(input_data, str):
            if os.path.isfile(input_data) and input_data.lower().endswith(('.txt', '.pdf','.docx')):
                return convert_to_text(input_data)
            else:
                # Not a file or unsupported extension, treat as raw text
                return input_data
        else:
            raise ValueError("L'entrée doit être une chaîne de caractères (chemin ou texte brut).")


    def compute_similarity(self, text1, text2) -> float:
        """
        Calcule la similarité cosinus entre deux textes via SBERT.

        Args:
        - text1 (str): Premier texte ou chemin vers un fichier.
        - text2 (str): Deuxième texte ou chemin vers un fichier.

        Returns:
        - float: Score de similarité cosinus entre les deux textes.
        """
        t1 = self.process_input(text1)
        t2 = self.process_input(text2)
        # print("t1",t1)

        emb1 = self.model.encode(t1, convert_to_tensor=True)
        emb2 = self.model.encode(t2, convert_to_tensor=True)

        cosine_sim = util.pytorch_cos_sim(emb1, emb2).item()
        return cosine_sim

    def batch_similarity(self, pairs):
        """
        Calcule les similarités pour une liste de paires (text1, text2).

        Args:
        - pairs (list[tuple[str, str]]): Liste de paires de textes ou chemins de fichiers.

        Returns:
        - list[float or None]: Liste des scores de similarité, None en cas d’erreur.
        """
        results = []
        for text1, text2 in pairs:
            try:
                score = self.compute_similarity(text1, text2)
            except Exception as e:
                print(f"Erreur pour la paire ({text1}, {text2}) : {e}")
                score = None
            results.append(score)
        return results
    
    # comparer deux textes directement
    def compute_similarity_from_texts(self, cv_text, job_text):
        cv_embedding = self.model.encode(cv_text, convert_to_tensor=True)
        job_embedding = self.model.encode(job_text, convert_to_tensor=True)
        similarity = util.cos_sim(cv_embedding, job_embedding)
        return float(similarity[0][0])
