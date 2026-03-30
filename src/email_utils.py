"""
src/email_utils.py — OTP email sending via SMTP.
Configure via environment variables:
  SMTP_HOST, SMTP_PORT (default 465), SMTP_USER, SMTP_PASSWORD, OTP_FROM_EMAIL
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_otp_email(to_email: str, code: str) -> bool:
    """Send OTP via SMTP. Returns True on success."""
    host       = os.environ.get("SMTP_HOST")
    port       = int(os.environ.get("SMTP_PORT", "465"))
    user       = os.environ.get("SMTP_USER")
    password   = os.environ.get("SMTP_PASSWORD")
    from_email = os.environ.get("OTP_FROM_EMAIL", user)

    if not all([host, user, password, from_email]):
        # Dev fallback: print OTP to console
        print(f"[DEV] OTP for {to_email}: {code}")
        return False

    msg = EmailMessage()
    msg["Subject"] = "Your AI Study Tracker OTP"
    msg["From"]    = from_email
    msg["To"]      = to_email
    msg.set_content(
        f"Your one-time login code is: {code}\n\n"
        "It expires in a few minutes. Do not share this with anyone."
    )

    try:
        with smtplib.SMTP_SSL(host, port) as server:
            server.login(user, password)
            server.send_message(msg)
        return True
    except smtplib.SMTPException as exc:
        print(f"[EMAIL ERROR] {exc}")
        return False
