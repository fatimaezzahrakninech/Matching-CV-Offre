import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from joblib import load
import fitz  # PyMuPDF
from utils import nettoyer_texte
from collections import Counter

# 📂 Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MODEL_FOLDER = BASE_DIR  # Tous les modèles sont dans Detect_Domain
ALLOWED_EXTENSIONS = {"pdf"}

# 🔁 Chargement des modèlesimport os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from joblib import load
import fitz  # PyMuPDF
from docx import Document
from utils import nettoyer_texte
from collections import Counter

# 📂 Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MODEL_FOLDER = BASE_DIR
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# 🔁 Chargement des modèles
svm_model = load(os.path.join(MODEL_FOLDER, "https://drive.google.com/uc?export=download&id=11JYM7STbtJ3yJUSI-qfnH0huPUkckuLF"))
knn_model = load(os.path.join(MODEL_FOLDER, "https://drive.google.com/uc?export=download&id=1RBGlw_7FOVQbYBnrzyJZzekvzdUUbpVE"))
rf_model = load(os.path.join(MODEL_FOLDER, "https://drive.google.com/uc?export=download&id=11RKWrxTjsOh-S8qKDDZJhqXEJB3k6g6O"))
dt_model = load(os.path.join(MODEL_FOLDER, "https://drive.google.com/uc?export=download&id=1t-hEyCez5u-3C9PaKIhX_tHFvAbqBf87"))
vectorizer = load(os.path.join(MODEL_FOLDER, "https://drive.google.com/uc?export=download&id=1AHyGNsnPg-awgl4oszXM1eGJtJ1pcvxa"))
class_names = load(os.path.join(MODEL_FOLDER, "https://drive.google.com/uc?export=download&id=1JY_EVrCEr0qlmLXNTh8-XOxX1yTtbpdA"))

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 📄 Vérifie l’extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🔍 Détection du type de mise en page PDF
def detecter_type_cv(filepath):
    with fitz.open(filepath) as doc:
        for page in doc:
            blocs = page.get_text("blocks", sort=True)
            positions_x = [bloc[0] for bloc in blocs]
            largeur_page = page.rect.width
            positions_x_filtrees = [x for x in positions_x if 50 < x < largeur_page - 50]
            if not positions_x_filtrees:
                continue
            ecarts_x = [abs(positions_x_filtrees[i+1] - positions_x_filtrees[i]) for i in range(len(positions_x_filtrees)-1)]
            if ecarts_x and max(ecarts_x) > largeur_page / 2.5:
                return "2_colonnes"
    return "1_colonne"

# 📄 Extraction depuis PDF
def extraire_depuis_pdf(filepath):
    type_cv = detecter_type_cv(filepath)
    texte = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            blocs = page.get_text("blocks", sort=True)
            largeur_page = page.rect.width
            if type_cv == "2_colonnes":
                blocs_gauche = []
                blocs_droite = []
                for bloc in blocs:
                    x0 = bloc[0]
                    if x0 < largeur_page / 2:
                        blocs_gauche.append(bloc[4])
                    else:
                        blocs_droite.append(bloc[4])
                texte += '\n'.join(blocs_gauche + blocs_droite) + "\n"
            else:
                for bloc in blocs:
                    texte += bloc[4] + "\n"
    return nettoyer_texte(texte)

# 📄 Extraction depuis DOCX
def extraire_depuis_docx(filepath):
    doc = Document(filepath)
    texte = "\n".join([para.text for para in doc.paragraphs])
    return nettoyer_texte(texte)

# 📄 Extraction depuis TXT
def extraire_depuis_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        texte = f.read()
    return nettoyer_texte(texte)

# 🧠 Extraction du texte selon le type
def extraire_texte(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == "pdf":
        return extraire_depuis_pdf(filepath)
    elif ext == "docx":
        return extraire_depuis_docx(filepath)
    elif ext == "txt":
        return extraire_depuis_txt(filepath)
    else:
        return ""

# 🚀 API : détection du domaine
@app.route("/detect-domain", methods=["POST"])
def detect_domain():
    if "cv_file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["cv_file"]
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(path)

    texte_global = extraire_texte(path)
    vect = vectorizer.transform([texte_global])

    predictions = {
        "SVM": class_names[svm_model.predict(vect)[0]],
        "KNN": class_names[knn_model.predict(vect)[0]],
        "RandomForest": class_names[rf_model.predict(vect)[0]],
        "DecisionTree": class_names[dt_model.predict(vect)[0]]
    }

    counts = Counter(predictions.values())
    if counts.most_common(1)[0][1] >= 2:
        domaine_final = counts.most_common(1)[0][0]
    else:
        rf = predictions["RandomForest"]
        knn = predictions["KNN"]
        domaine_final = f"{rf} / {knn}"

    return jsonify({"domaine": domaine_final})

if __name__ == "__main__":
    app.run(debug=True)

svm_model = load(os.path.join(MODEL_FOLDER, "svm_model.joblib"))
knn_model = load(os.path.join(MODEL_FOLDER, "knn_model.joblib"))
rf_model = load(os.path.join(MODEL_FOLDER, "random_forest_model.joblib"))
dt_model = load(os.path.join(MODEL_FOLDER, "decision_tree_model.joblib"))
vectorizer = load(os.path.join(MODEL_FOLDER, "tfidf_vectorizer.joblib"))
class_names = load(os.path.join(MODEL_FOLDER, "class_names.joblib"))

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 📄 Vérifie l’extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🔍 Détection du type de mise en page
def detecter_type_cv(filepath):
    with fitz.open(filepath) as doc:
        for page in doc:
            blocs = page.get_text("blocks", sort=True)
            positions_x = [bloc[0] for bloc in blocs]
            largeur_page = page.rect.width
            positions_x_filtrees = [x for x in positions_x if 50 < x < largeur_page - 50]
            if not positions_x_filtrees:
                continue
            ecarts_x = [abs(positions_x_filtrees[i+1] - positions_x_filtrees[i]) for i in range(len(positions_x_filtrees)-1)]
            if ecarts_x and max(ecarts_x) > largeur_page / 2.5:
                return "2_colonnes"
    return "1_colonne"

# 🧠 Extraction du texte
def extraire_texte(filepath):
    type_cv = detecter_type_cv(filepath)
    texte = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            blocs = page.get_text("blocks", sort=True)
            largeur_page = page.rect.width
            if type_cv == "2_colonnes":
                blocs_gauche = []
                blocs_droite = []
                for bloc in blocs:
                    x0 = bloc[0]
                    if x0 < largeur_page / 2:
                        blocs_gauche.append(bloc[4])
                    else:
                        blocs_droite.append(bloc[4])
                texte += '\n'.join(blocs_gauche + blocs_droite) + "\n"
            else:
                for bloc in blocs:
                    texte += bloc[4] + "\n"
    return nettoyer_texte(texte)

# 🚀 API : détection du domaine
@app.route("/detect-domain", methods=["POST"])
def detect_domain():
    if "cv_pdf" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["cv_pdf"]
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(path)

    texte_global = extraire_texte(path)
    vect = vectorizer.transform([texte_global])

    # 🔎 Prédictions
    predictions = {
        "SVM": class_names[svm_model.predict(vect)[0]],
        "KNN": class_names[knn_model.predict(vect)[0]],
        "RandomForest": class_names[rf_model.predict(vect)[0]],
        "DecisionTree": class_names[dt_model.predict(vect)[0]]
    }

    # 🧠 Consensus ou fallback
    counts = Counter(predictions.values())
    if counts.most_common(1)[0][1] >= 2:
        domaine_final = counts.most_common(1)[0][0]
    else:
        rf = predictions["RandomForest"]
        knn = predictions["KNN"]
        domaine_final = f"{rf} / {knn}"

    return jsonify({"domaine": domaine_final})

if __name__ == "__main__":
    app.run(debug=True)
