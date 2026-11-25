from __future__ import annotations

import asyncio
import os
import smtplib
import ssl
from email.message import EmailMessage

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/support", tags=["support"])

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
    message["Subject"] = f"[FlowForge problem report] {report.kind}: {report.subject}"
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


@router.post("/problem-reports", status_code=202)
async def submit_problem_report(report: ProblemReport) -> dict[str, str]:
    try:
        await asyncio.to_thread(_send, report)
    except (OSError, RuntimeError, smtplib.SMTPException) as exc:
        raise HTTPException(
            status_code=503, detail="Problem report delivery is unavailable"
        ) from exc
    return {"status": "accepted", "message": "Thank you for helping us improve the website."}
