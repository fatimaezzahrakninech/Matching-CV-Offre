import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from Sbert.SBERTMatching import SBERTMatching
from Skill2Vec.Skill2VecMatching import Skill2VecMatching
from utils.preprocess import preprocess
from utils.extract_profile_elements import extract_structured_elements
from language_adapter import adapt_texts

# 📂 Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# 🔁 Chargement des modèles
sbert_model_path = "https://drive.google.com/uc?export=download&id=1KPuaQuwp4gEQZv6HwpVm8CHtJm3qr03Z"
skill2vec_model_path = "https://drive.google.com/uc?export=download&id=1Orr6HYjK6fAIhSM32iRAv5qpnqLwsvoh"
sbert_matcher = SBERTMatching(model_path=sbert_model_path)
skill2vec_matcher = Skill2VecMatching(model_path=skill2vec_model_path)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 📄 Vérifie l’extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🧠 Offre par défaut (à personnaliser selon ton contexte)
def get_default_offer():
    return """
    Nous recherchons un profil polyvalent avec des compétences en gestion de projet, maîtrise des outils bureautiques,
    capacité d’analyse, et aisance en communication. Une expérience en environnement agile est un plus.
    """

# 🔍 Calcul du score d’extraction
def compute_extraction_score(cv_data, job_data):
    def coverage_ratio(cv_list, job_list):
        if not job_list:
            return None
        if not cv_list:
            return 0.0
        matched = [item for item in job_list if item.lower() in [c.lower() for c in cv_list]]
        return len(matched) / len(job_list)

    skill_score = coverage_ratio(cv_data["competences"], job_data["competences"])
    soft_score = coverage_ratio(cv_data["soft_skills"], job_data["soft_skills"])
    lang_score = coverage_ratio(cv_data["languages"], job_data["languages"])

    weights = {"skills": 0.6 if skill_score is not None else 0.0,
               "soft": 0.3 if soft_score is not None else 0.0,
               "lang": 0.1 if lang_score is not None else 0.0}
    total_weight = sum(weights.values())

    score = 0.0
    if skill_score is not None:
        score += weights["skills"] * skill_score
    if soft_score is not None:
        score += weights["soft"] * soft_score
    if lang_score is not None:
        score += weights["lang"] * lang_score

    return round(score / total_weight if total_weight > 0 else 1.0, 4)

# 🚀 API : matching automatique
@app.route("/match-profile", methods=["POST"])
def match_profile():
    if "cv_file" not in request.files:
        return jsonify({"error": "Missing CV file"}), 400

    file = request.files["cv_file"]
    job_text_raw = request.form.get("job_text", get_default_offer())

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    with open(path, "wb") as f:
        f.write(file.read())

    job_text_original = preprocess(job_text_raw)
    cv_text_original = sbert_matcher.process_input(path)
    cv_text_translated, job_text_translated = adapt_texts(cv_text_original, job_text_original)

    score_sbert = sbert_matcher.compute_similarity_from_texts(cv_text_translated, job_text_translated)
    score_skill2vec = skill2vec_matcher.get_similarity_score(cv_input=path, job_input=job_text_original)

    cv_structured = extract_structured_elements(cv_text_original)
    job_structured = extract_structured_elements(job_text_original)
    score_extraction = compute_extraction_score(cv_structured, job_structured)

    # Pondération adaptative
    if score_sbert > 0.75 and score_skill2vec > 0.80:
        alpha, beta, gamma = 0.6, 0.4, 0.0
    elif score_sbert > 0.75:
        alpha, beta, gamma = 0.8, 0.2, 0.0
    elif score_skill2vec > 0.75 and score_extraction > 0.75 and score_sbert < 0.75:
        alpha, beta, gamma = 0.4, 0.4, 0.2
    elif score_skill2vec >= 0.75 and score_sbert >= 0.60:
        alpha, beta, gamma = 0.2, 0.8, 0.0
    else:
        alpha = 0.6
        beta = 0.35 if score_extraction < 0.5 else 0.3
        gamma = 0.05 if score_extraction < 0.5 else 0.1

    score_final = round(alpha * score_sbert + beta * score_skill2vec + gamma * score_extraction, 4)
    score_percent = int(score_final * 100)

    if score_final > 0.75:
        verdict = "Très bon match"
    elif score_final > 0.5:
        verdict = "Match partiel"
    else:
        verdict = "Faible compatibilité"

    return jsonify({
        "score": score_percent,
        "verdict": verdict
    })

if __name__ == "__main__":
    app.run(debug=True)
