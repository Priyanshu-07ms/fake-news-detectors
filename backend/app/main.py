# app/main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import re
from newspaper import Article

from .database import SessionLocal, engine
from .models import Base, Prediction
from . import schemas
from .ml_model import predict_text

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fake News Detection API", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# DB
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# RULES
# =========================

SUSPICIOUS_PATTERNS = [
    "forward this",
    "viral message",
    "miracle cure",
    "government is hiding",
    "share this",
]

PM_PATTERN = re.compile(
    r"(.+?)\s+is\s+the\s+prime\s+minister\s+of\s+india",
    re.IGNORECASE
)

def apply_rules(text: str):
    lower = text.lower()

    if len(text.split()) < 8:
        return True, "uncertain", 0.0, 0.0, "Text too short"

    pm_match = PM_PATTERN.search(lower)
    if pm_match:
        person = pm_match.group(1).strip()
        if "narendra modi" in person:
            return True, "real", 0.1, 0.9, "Correct PM detected"
        else:
            return True, "fake", 0.9, 0.1, "Incorrect PM claim"

    for p in SUSPICIOUS_PATTERNS:
        if p in lower:
            return True, "fake", 0.9, 0.1, f"Suspicious phrase: {p}"

    return False, "", 0.0, 0.0, ""


# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return {"message": "Fake News Detection API Running"}


# =========================
# 🔥 SINGLE MODEL PREDICT
# =========================

@app.post("/predict", response_model=schemas.PredictResponse)
def predict(req: schemas.PredictRequest, db: Session = Depends(get_db)):

    text = req.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    rule_applied, label, pf, pr, reason = apply_rules(text)

    if not rule_applied:
        label, pf, pr, top_words = predict_text(text, req.model)
        message = f"Important words: {', '.join(top_words)}"
    else:
        message = reason

    confidence = max(pf, pr) * 100

    pred = Prediction(
        text=text,
        predicted_label=label,
        confidence=confidence,
        prob_fake=pf * 100,
        prob_real=pr * 100,
    )

    db.add(pred)
    db.commit()
    db.refresh(pred)

    return schemas.PredictResponse(
        id=pred.id,
        label=label,
        confidence=round(confidence, 2),
        prob_fake=round(pf * 100, 2),
        prob_real=round(pr * 100, 2),
        message=message,
        model=req.model
    )


# =========================
# 🔥 MULTI MODEL COMPARISON
# =========================

@app.post("/predict-all", response_model=schemas.MultiPredictResponse)
def predict_all(req: schemas.PredictRequest):

    text = req.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    models = ["logreg", "nb", "svm", "bert"]
    results = {}

    for m in models:
        try:
            label, pf, pr, _ = predict_text(text, m)

            results[m] = {
                "label": label,
                "confidence": round(max(pf, pr) * 100, 2),
                "prob_fake": round(pf * 100, 2),
                "prob_real": round(pr * 100, 2),
            }
        except Exception as e:
            results[m] = {"error": str(e)}

    return {"results": results}


# =========================
# 🔥 URL ANALYSIS
# =========================

@app.post("/predict-url")
def predict_url(req: schemas.URLRequest):

    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        article = Article(req.url)
        article.download()
        article.parse()

        text = article.text

        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text")

        label, pf, pr, top_words = predict_text(text, req.model)

        return {
            "label": label,
            "confidence": round(max(pf, pr) * 100, 2),
            "prob_fake": round(pf * 100, 2),
            "prob_real": round(pr * 100, 2),
            "message": f"Important words: {', '.join(top_words)}",
            "preview": text[:300],
            "model": req.model
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# 🔥 FEEDBACK LOOP
# =========================

@app.post("/feedback")
def feedback(req: schemas.FeedbackRequest, db: Session = Depends(get_db)):

    pred = db.query(Prediction).filter(Prediction.id == req.prediction_id).first()

    if not pred:
        return {"error": "Not found"}

    pred.user_feedback = req.user_feedback
    pred.correct_label = req.correct_label

    db.commit()

    # 🔥 STORE MISCLASSIFIED DATA
    if req.user_feedback == "incorrect":
        with open("retrain_data.txt", "a", encoding="utf-8") as f:
            f.write(f"{pred.text} || {req.correct_label}\n")

    return {"status": "saved"}