import re

def nettoyer_texte(texte):
    # Supprimer les espaces multiples
    texte = re.sub(r"\s+", " ", texte)

    # Supprimer les caractères spéciaux inutiles
    texte = re.sub(r"[•▪●♦■▶→]", "", texte)

    # Supprimer les ponctuations isolées
    texte = re.sub(r"[^\w\s@.+]", "", texte)

    # Séparer les mots collés par majuscules (ex : STAGEEN → STAGE EN)
    texte = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", texte)

    return texte.strip()
