from pydantic import BaseModel

class PredictRequest(BaseModel):
    text: str
    model: str = "logreg"   # 🔥 ADD THIS

class PredictResponse(BaseModel):
    id: int | None = None
    label: str
    confidence: float
    prob_fake: float
    prob_real: float
    message: str | None = None

class FeedbackRequest(BaseModel):
    prediction_id: int
    user_feedback: str
    correct_label: str | None = None

class URLRequest(BaseModel):
    url: str
    
class MultiPredictResponse(BaseModel):
    results: dict