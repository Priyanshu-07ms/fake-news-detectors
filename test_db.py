# app/test_db.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import engine, SessionLocal
from .models import Base

def test_connection():
    print("Creating tables (if not exist)...")
    Base.metadata.create_all(bind=engine)
    print("Tables created or already exist.")

    db: Session = SessionLocal()
    try:
        # ✅ SQLAlchemy 2.x: wrap raw SQL in text()
        db.execute(text("SELECT 1"))
        print("✅ Database connection OK!")
    except Exception as e:
        print("❌ Database connection FAILED:")
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
