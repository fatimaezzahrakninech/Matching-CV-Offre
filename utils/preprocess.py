import re

def preprocess(text):
    text = text.lower()
    text = text.replace('\n', ' ').replace('\r', ' ')
    
    # Supprimer les mots coupés par des tirets (ex: "déve-\nloppeur")
    text = re.sub(r'-\s+', '', text)
    
    # Garder certains caractères techniques utiles
    text = re.sub(r'[^\w\s\-\+#:/.,]', ' ', text)
    
    # Supprimer les headers/footers répétitifs (ex: "page 1", "confidentiel", etc.)
    text = re.sub(r'\b(page\s*\d+|confidentiel|curriculum vitae)\b', '', text)
    
    # Réduire les espaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text