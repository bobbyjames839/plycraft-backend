import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json

router = APIRouter()

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
Base = declarative_base()

class NewsletterSignup(Base):
    __tablename__ = "newsletter_signups"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(120))
    last_name = Column(String(120))
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class SignupIn(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr


def init_tables():
    if engine is None:
        return
    Base.metadata.create_all(bind=engine)


@router.on_event("startup")
def on_startup():
    init_tables()


@router.post("/newsletter/signup")
def newsletter_signup(payload: SignupIn):
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    session = SessionLocal()
    try:
        # Check for existing email
        existing = session.query(NewsletterSignup).filter(NewsletterSignup.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already signed up")

        row = NewsletterSignup(
            first_name=payload.firstName.strip(),
            last_name=payload.lastName.strip(),
            email=payload.email.strip().lower(),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return {"ok": True, "id": row.id}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to save signup")
    finally:
        session.close()



@router.get("/newsletter/export")
def export_newsletter_signups():
    if SessionLocal is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    session = SessionLocal()
    try:
        # Query all signups
        signups = session.query(NewsletterSignup).all()

        # Convert signups to a list of dictionaries
        data = [
            {
                "id": signup.id,
                "first_name": signup.first_name,
                "last_name": signup.last_name,
                "email": signup.email,
                "created_at": signup.created_at.isoformat(),
            }
            for signup in signups
        ]

        # Save data to a JSON file
        with open("newsletter_signups.json", "w") as file:
            json.dump(data, file, indent=4)

        return {"ok": True, "message": "Data exported to newsletter_signups.json"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {e}")
    finally:
        session.close()
