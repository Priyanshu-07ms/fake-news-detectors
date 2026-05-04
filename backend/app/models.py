# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    predicted_label = Column(String, nullable=False)  # "fake" or "real"
    confidence = Column(Float, nullable=False)        # percentage 0–100
    prob_fake = Column(Float, nullable=False)
    prob_real = Column(Float, nullable=False)
    user_feedback = Column(String, nullable=True)     # e.g., "correct", "incorrect", or custom
    correct_label = Column(String, nullable=True)     # if user tells us the correct label
    created_at = Column(DateTime(timezone=True), server_default=func.now())
