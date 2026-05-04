# app/ml_model.py

import os
import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS = os.path.join(BASE_DIR, "artifacts")

# =========================
# LOAD VECTORIZER
# =========================
vectorizer = joblib.load(os.path.join(ARTIFACTS, "tfidf_vectorizer.joblib"))

# =========================
# LOAD MODELS
# =========================
logreg_model = joblib.load(os.path.join(ARTIFACTS, "logreg_model.joblib"))

nb_model = None
svm_model = None
rf_model = None

try:
    nb_model = joblib.load(os.path.join(ARTIFACTS, "nb_model.joblib"))
    print("Naive Bayes loaded ✅")
except:
    print("NB model not found")

try:
    svm_model = joblib.load(os.path.join(ARTIFACTS, "svm_model.joblib"))
    print("SVM loaded ✅")
except:
    print("SVM model not found")

try:
    rf_model = joblib.load(os.path.join(ARTIFACTS, "rf_model.joblib"))
    print("Random Forest loaded ✅")
except:
    print("RF model not found")


# =========================
# 🔥 HELPERS
# =========================

def get_top_words(text, top_n=5):
    vec = vectorizer.transform([text])
    feature_names = vectorizer.get_feature_names_out()

    scores = vec.toarray()[0]
    top_indices = scores.argsort()[-top_n:][::-1]

    return [feature_names[i] for i in top_indices if scores[i] > 0]


# 🔥 Suspicion detector
def suspicious_text(text):
    patterns = [
        "reportedly",
        "sources say",
        "claims that",
        "miracle",
        "cure",
        "secret",
        "leaked",
        "undisclosed",
        "study shows",
        "experts say"
    ]

    text = text.lower()
    return any(p in text for p in patterns)


# 🔥 Calibration
def calibrate_probs(pf, pr):
    pf = pow(pf, 0.9)
    pr = pow(pr, 0.9)

    total = pf + pr
    return pf / total, pr / total


# 🔥 Uncertainty logic
def apply_uncertainty(pf, pr):
    confidence = max(pf, pr)

    # stricter threshold
    if confidence < 0.70:
        return "uncertain"

    return "real" if pr > pf else "fake"


# =========================
# 🔥 MAIN FUNCTION
# =========================

def predict_text(text: str, model_name="logreg"):

    if not text.strip():
        return "unknown", 0.0, 0.0, []

    vec = vectorizer.transform([text])

    # =========================
    # 🔥 MODEL SELECTION
    # =========================
    if model_name == "nb" and nb_model:
        model = nb_model

    elif model_name == "svm" and svm_model:
        model = svm_model

    elif model_name == "rf" and rf_model:
        model = rf_model

    else:
        model = logreg_model

    probs = model.predict_proba(vec)[0]

    pf = float(probs[0])
    pr = float(probs[1])

    # =========================
    # 🔥 CALIBRATION
    # =========================
    pf, pr = calibrate_probs(pf, pr)

    # =========================
    # 🔥 BASE LABEL
    # =========================
    label = apply_uncertainty(pf, pr)

    # =========================
    # 🔥 SUSPICIOUS TEXT CHECK
    # =========================
    if suspicious_text(text):
        if max(pf, pr) > 0.7:
            label = "uncertain"

    # =========================
    # 🔥 ENSEMBLE CHECK (RF vs LOGREG)
    # =========================
    try:
        lr_probs = logreg_model.predict_proba(vec)[0]

        lr_fake = float(lr_probs[0])
        lr_real = float(lr_probs[1])

        # disagreement → uncertain
        if (pr > pf and lr_fake > lr_real) or (pf > pr and lr_real > lr_fake):
            label = "uncertain"
    except:
        pass

    # =========================
    # 🔥 CAP EXTREME CONFIDENCE
    # =========================
    if max(pf, pr) > 0.95:
        pf *= 0.95
        pr *= 0.95

    # =========================
    # 🔥 EXPLANATION
    # =========================
    top_words = get_top_words(text)

    return label, pf, pr, top_words