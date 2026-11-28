from __future__ import annotations

import asyncio
import json
import logging
import os
import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/support", tags=["support"])
logger = logging.getLogger("flowforge.support")

_RECIPIENT = os.getenv("FLOWFORGE_SUPPORT_RECIPIENT", "mackburba12@outlook.com")


class ProblemReport(BaseModel):
    kind: str = Field(min_length=2, max_length=80)
    subject: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=4000)
    steps_to_reproduce: str | None = Field(default=None, max_length=2500)
    reporter_email: str | None = Field(default=None, max_length=320)
    page_url: str = Field(max_length=1000)
    user_agent: str = Field(max_length=1000)


def _send(report: ProblemReport) -> None:
    host = os.getenv("FLOWFORGE_SUPPORT_SMTP_HOST", "smtp-mail.outlook.com")
    port = int(os.getenv("FLOWFORGE_SUPPORT_SMTP_PORT", "587"))
    username = os.getenv("FLOWFORGE_SUPPORT_SMTP_USERNAME")
    password = os.getenv("FLOWFORGE_SUPPORT_SMTP_PASSWORD")
    sender = os.getenv("FLOWFORGE_SUPPORT_FROM", username or "")
    if not username or not password or not sender:
        raise RuntimeError("Support email delivery is not configured")

    message = EmailMessage()
    message["Subject"] = f"[Krov WorkAgent problem report] {report.kind}: {report.subject}"
    message["From"] = sender
    message["To"] = _RECIPIENT
    if report.reporter_email:
        message["Reply-To"] = str(report.reporter_email)
    message.set_content(
        "\n".join(
            [
                f"Type: {report.kind}",
                f"Summary: {report.subject}",
                f"Reporter: {report.reporter_email or 'Not provided'}",
                f"Page: {report.page_url}",
                f"Browser: {report.user_agent}",
                "",
                "Description:",
                report.description,
                "",
                "Steps to reproduce:",
                report.steps_to_reproduce or "Not provided",
            ]
        )
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=20) as client:
        client.ehlo()
        client.starttls(context=context)
        client.ehlo()
        client.login(username, password)
        client.send_message(message)


def _spool(report: ProblemReport) -> str:
    """Keep an undelivered report in the support outbox so it is never lost."""
    outbox = Path(os.getenv("FLOWFORGE_SUPPORT_OUTBOX", "var/support-outbox"))
    outbox.mkdir(parents=True, exist_ok=True)
    reference = f"{datetime.now(UTC):%Y%m%dT%H%M%S}-{uuid4().hex[:8]}"
    record = {
        "reference": reference,
        "received_at": datetime.now(UTC).isoformat(),
        **report.model_dump(),
    }
    (outbox / f"{reference}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return reference


@router.post("/problem-reports", status_code=202)
async def submit_problem_report(report: ProblemReport) -> dict[str, str]:
    try:
        await asyncio.to_thread(_send, report)
    except (OSError, RuntimeError, smtplib.SMTPException) as exc:
        # Delivery is unavailable (not configured or the mail server failed): queue it.
        reference = await asyncio.to_thread(_spool, report)
        logger.warning(
            "Problem report %s queued; delivery failed: %s", reference, type(exc).__name__
        )
        return {
            "status": "queued",
            "reference": reference,
            "message": "Thank you. Your report was saved and will be delivered to support.",
        }
    return {"status": "accepted", "message": "Thank you for helping us improve the website."}
