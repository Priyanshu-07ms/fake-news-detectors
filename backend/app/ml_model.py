# app/ml_model.py

import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS = os.path.join(BASE_DIR, "artifacts")

vectorizer = joblib.load(os.path.join(ARTIFACTS, "tfidf_vectorizer.joblib"))

logreg_model = joblib.load(os.path.join(ARTIFACTS, "logreg_model.joblib"))

nb_model = None
svm_model = None

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

# ------------------------
# DistilBERT
# ------------------------
USE_BERT = False
distilbert_path = os.path.join(ARTIFACTS, "distilbert")

if os.path.isdir(distilbert_path):
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch

        tokenizer = AutoTokenizer.from_pretrained(distilbert_path)
        bert_model = AutoModelForSequenceClassification.from_pretrained(distilbert_path)
        bert_model.eval()

        USE_BERT = True
        print("DistilBERT loaded ✅")
    except Exception as e:
        print("BERT load failed:", e)


def get_top_words(text, top_n=5):
    vec = vectorizer.transform([text])
    feature_names = vectorizer.get_feature_names_out()

    scores = vec.toarray()[0]
    top_indices = scores.argsort()[-top_n:][::-1]

    return [feature_names[i] for i in top_indices if scores[i] > 0]


# 🔥 MAIN FUNCTION (FIXED)
def predict_text(text: str, model_name="logreg"):

    print("MODEL USED:", model_name)  # 🔥 DEBUG

    if not text.strip():
        return "unknown", 0.0, 0.0, []

    # 🔥 BERT
    if model_name == "bert" and USE_BERT:
        print("USING BERT")

        import torch

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256
        )

        with torch.no_grad():
            outputs = bert_model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1).numpy()[0]

        prob_fake = float(probs[0])
        prob_real = float(probs[1])

    else:
        vec = vectorizer.transform([text])

        if model_name == "nb" and nb_model:
            print("USING NB")
            model = nb_model

        elif model_name == "svm" and svm_model:
            print("USING SVM")
            model = svm_model

        else:
            print("USING LOGREG")
            model = logreg_model

        probs = model.predict_proba(vec)[0]
        prob_fake = float(probs[0])
        prob_real = float(probs[1])

    label = "real" if prob_real > prob_fake else "fake"
    top_words = get_top_words(text)

    return label, prob_fake, prob_real, top_words