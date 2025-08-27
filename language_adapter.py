from langdetect import detect
from deep_translator import GoogleTranslator

# 🔍 Détection de la langue
def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

# ✂️ Découpage du texte en segments < 5000 caractères
def split_text(text, max_length=5000):
    segments = []
    while len(text) > max_length:
        split_index = text[:max_length].rfind('.') + 1  # coupe à la fin d'une phrase
        if split_index == 0:
            split_index = max_length
        segments.append(text[:split_index].strip())
        text = text[split_index:].strip()
    segments.append(text)
    return segments

# 🌐 Traduction segmentée
def translate_long_text(text, source_lang='fr', target_lang='en'):
    segments = split_text(text)
    translated_segments = [
        GoogleTranslator(source=source_lang, target=target_lang).translate(seg)
        for seg in segments
    ]
    return ' '.join(translated_segments)

# 🔁 Traduction conditionnelle
def translate_to_english(text, source_lang):
    if source_lang == "fr":
        return translate_long_text(text, source_lang, "en")
    return text  # No translation needed

# 🧩 Traduction ciblée des compétences extraites
def translate_skills_to_english(skills_list, source_lang):
    if source_lang == "fr":
        return [GoogleTranslator(source="fr", target="en").translate(skill) for skill in skills_list]
    return skills_list  # Pas de traduction nécessaire

# 🧠 Adaptation des textes CV / Offre
def adapt_texts(cv_text, offer_text):
    cv_lang = detect_language(cv_text)
    offer_lang = detect_language(offer_text)

    # ✅ Traduire en anglais si le texte est en français
    adapted_cv = translate_to_english(cv_text, cv_lang)
    adapted_offer = translate_to_english(offer_text, offer_lang)

    return adapted_cv, adapted_offer

# 🧠 Adaptation des compétences extraites
def adapt_skills(cv_skills, offer_skills, cv_text, offer_text):
    cv_lang = detect_language(cv_text)
    offer_lang = detect_language(offer_text)

    translated_cv_skills = translate_skills_to_english(cv_skills, cv_lang)
    translated_offer_skills = translate_skills_to_english(offer_skills, offer_lang)

    return translated_cv_skills, translated_offer_skills
