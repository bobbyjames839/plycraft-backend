import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


class ContactIn(BaseModel):
    firstName: str = Field(min_length=1)
    lastName: str = Field(min_length=1)
    email: EmailStr
    phone: str | None = None
    product: str | None = None
    subject: str | None = None
    message: str = Field(min_length=1)


def send_mail(subject: str, body: str, *, to_email: str, from_email: str) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")

    if not (username and password):
        raise RuntimeError("SMTP credentials are not configured")

    msg = EmailMessage()
    # Use the sender provided by the frontend form
    msg["From"] = from_email
    # Ensure replies go back to the sender as well
    msg["Reply-To"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(msg)


@router.post("/contact/send")
def contact_send(payload: ContactIn):
    to_email = os.getenv("MAIL_TO")

    subject = payload.subject or "New contact message from PlyCraft"
    body = (
        f"Name: {payload.firstName} {payload.lastName}\n"
        f"Email: {payload.email}\n"
        f"Phone: {payload.phone or '-'}\n"
        f"Product: {payload.product or '-'}\n\n"
        f"Message:\n{payload.message}\n"
    )

    try:
        # Always send to your inbox, and set From to the user's email from the form
        send_mail(subject, body, to_email=to_email, from_email=str(payload.email))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
