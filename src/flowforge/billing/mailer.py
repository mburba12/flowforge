"""Outgoing email (invoices). Without SMTP settings, mail is written to the outbox folder
so nothing is lost and it can be sent by hand."""

import json
import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4

from starlette.concurrency import run_in_threadpool

from flowforge.core.config import settings


class MailNotSent(RuntimeError):
    pass


def configured() -> bool:
    return bool(settings.smtp_host and settings.mail_from)


def _send(message: EmailMessage) -> None:
    context = ssl.create_default_context()
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(
            settings.smtp_host, settings.smtp_port, timeout=30, context=context
        ) as smtp:
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        return
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls(context=context)
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def _to_outbox(message: EmailMessage, reason: str) -> str:
    outbox = Path(settings.mail_outbox)
    outbox.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now(UTC):%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
    (outbox / f"{name}.eml").write_bytes(bytes(message))
    (outbox / f"{name}.json").write_text(
        json.dumps({"to": message["To"], "subject": message["Subject"], "reason": reason}),
        encoding="utf-8",
    )
    return name


async def send(to: list[str], subject: str, text_body: str, html_body: str) -> str:
    """Send; returns "sent" or "outbox:<name>" when SMTP is not configured.

    Raises MailNotSent when SMTP is configured but delivery failed (the message is kept
    in the outbox as well)."""
    message = EmailMessage()
    message["From"] = settings.mail_from or "Krov WorkAgent <billing@localhost>"
    message["To"] = ", ".join(to)
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")
    if not configured():
        return "outbox:" + _to_outbox(message, "SMTP not configured")
    try:
        await run_in_threadpool(_send, message)
    except (OSError, smtplib.SMTPException) as exc:
        _to_outbox(message, f"SMTP failed: {type(exc).__name__}")
        raise MailNotSent(f"Email could not be sent ({type(exc).__name__}).") from exc
    return "sent"
