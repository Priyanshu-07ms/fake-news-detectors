# app/main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import re
import requests
from bs4 import BeautifulSoup
from newspaper import Article

from .database import SessionLocal, engine
from .models import Base, Prediction
from . import schemas
from .ml_model import predict_text

# =========================
# INIT
# =========================

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TruthLens AI API",
    version="10.0.0",
)

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
    return {"message": "TruthLens AI Running 🚀"}

# =========================
# 🔥 SINGLE MODEL
# =========================

@app.post("/predict", response_model=schemas.PredictResponse)
def predict(req: schemas.PredictRequest, db: Session = Depends(get_db)):

    text = req.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    rule_applied, label, pf, pr, reason = apply_rules(text)

    if not rule_applied:
        label, pf, pr, top_words = predict_text(text, req.model)

        if max(pf, pr) < 0.6 or abs(pf - pr) < 0.1:
            label = "uncertain"

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
# 🔥 MULTI MODEL
# =========================

@app.post("/predict-all", response_model=schemas.MultiPredictResponse)
def predict_all(req: schemas.PredictRequest):

    text = req.text.strip()

    models = ["logreg", "nb", "svm", "rf"]
    results = {}

    for m in models:
        try:
            label, pf, pr, _ = predict_text(text, m)

            if max(pf, pr) < 0.6 or abs(pf - pr) < 0.1:
                label = "uncertain"

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
# 🔥 URL ANALYSIS (FINAL FINAL FIX)
# =========================

@app.post("/predict-url")
def predict_url(req: schemas.URLRequest):

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9",
        }

        response = requests.get(
            req.url,
            headers=headers,
            timeout=10,
            allow_redirects=True
        )

        html = response.text

        if not html or len(html) < 500:
            raise HTTPException(status_code=400, detail="Blocked page")

        # 🔥 LIVE PAGE DETECTION
        is_live_page = "/live/" in req.url or "live" in req.url

        # 🔥 Newspaper extraction
        try:
            article = Article("")
            article.set_html(html)
            article.parse()
            text = article.text
        except:
            text = ""

        # 🔥 FILTERED BeautifulSoup fallback
        if not text or len(text) < 100:
            soup = BeautifulSoup(html, "html.parser")

            paragraphs = [
                p.get_text()
                for p in soup.find_all("p")
                if len(p.get_text().split()) > 8
            ]

            text = " ".join(paragraphs)

        # 🔥 CLEAN TEXT
        text = text.lower()
        text = re.sub(r"<.*?>", " ", text)
        text = re.sub(r"http\S+|www\S+", " ", text)
        text = re.sub(r"[^a-zA-Z\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text.split()) < 20:
            raise HTTPException(status_code=400, detail="Weak content")

        # 🔥 MODEL
        label, pf, pr, top_words = predict_text(text, req.model)

        # 🔥 TRUSTED SOURCE BOOST
        trusted = ["bbc.com", "reuters.com", "theguardian.com"]

        if any(domain in req.url for domain in trusted):
            pr = min(pr + 0.15, 1.0)
            pf = max(pf - 0.15, 0.0)

            if pr > pf:
                label = "real"

        # 🔥 LIVE PAGE FIX (CRITICAL)
        if is_live_page:
            if max(pf, pr) < 0.85:
                label = "uncertain"

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
        print("🔥 ERROR:", e)
        raise HTTPException(status_code=500, detail="Could not analyze the URL")

# =========================
# 🔥 FEEDBACK
# =========================

@app.post("/feedback")
def feedback(req: schemas.FeedbackRequest, db: Session = Depends(get_db)):

    pred = db.query(Prediction).filter(Prediction.id == req.prediction_id).first()

    if not pred:
        return {"error": "Not found"}

    pred.user_feedback = req.user_feedback
    pred.correct_label = req.correct_label

    db.commit()

    return {"status": "saved"}