$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$Web = Join-Path $Root "web"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Topbar = Join-Path $Web "src\components\topbar.tsx"
$Form = Join-Path $Web "src\components\problem-report-form.tsx"
$Css = Join-Path $Web "src\app\globals.css"
$Router = Join-Path $Root "src\flowforge\support_feedback.py"
$Main = Join-Path $Root "src\flowforge\main.py"

foreach ($Path in @($Topbar, $Css, $Main, $Python)) {
  if (-not (Test-Path -LiteralPath $Path)) { throw "Run from FlowForge project root. Missing: $Path" }
}

$FormText = @'
"use client";

import { FormEvent, useState } from "react";

type Props = { open: boolean; onClose: () => void };

export function ProblemReportForm({ open, onClose }: Props) {
  const [kind, setKind] = useState("Bug");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);

  if (!open) return null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/support/problem-reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind,
          subject,
          description,
          steps_to_reproduce: steps || null,
          reporter_email: email || null,
          page_url: window.location.href,
          user_agent: navigator.userAgent,
        }),
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Submission failed");
      }
      setSubmitted(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to submit the report.");
    } finally {
      setBusy(false);
    }
  }

  function finish() {
    setSubmitted(false);
    setKind("Bug");
    setSubject("");
    setDescription("");
    setSteps("");
    setEmail("");
    setError("");
    onClose();
  }

  return (
    <div className="problem-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="problem-dialog" role="dialog" aria-modal="true" aria-labelledby="problem-title">
        {submitted ? (
          <div className="problem-thanks">
            <div className="problem-check">✓</div>
            <h2 id="problem-title">Report submitted</h2>
            <p>Thank you for helping us improve the website.</p>
            <button type="button" className="btn primary" onClick={finish}>Done</button>
          </div>
        ) : (
          <>
            <header><div><small>FLOWFORGE SUPPORT</small><h2 id="problem-title">Report a problem</h2><p>Share what happened so the FlowForge team can investigate.</p></div><button type="button" className="iconbtn" onClick={onClose}>X</button></header>
            <form onSubmit={submit}>
              <div className="problem-body">
                <div className="problem-grid">
                  <label><span>Problem type</span><select value={kind} onChange={(event) => setKind(event.target.value)}><option>Bug</option><option>Broken button or workflow</option><option>Incorrect data</option><option>Performance</option><option>Accessibility</option><option>Other</option></select></label>
                  <label><span>Reply email (optional)</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@company.com" /></label>
                </div>
                <label><span>Summary</span><input required maxLength={160} value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Briefly describe the problem" /></label>
                <label><span>What happened?</span><textarea required minLength={10} maxLength={4000} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Describe what you expected and what actually happened." rows={6} /></label>
                <label><span>Steps to reproduce (optional)</span><textarea maxLength={2500} value={steps} onChange={(event) => setSteps(event.target.value)} placeholder="1. Open Orders&#10;2. Select a record&#10;3. Click Edit" rows={4} /></label>
                <p className="problem-privacy">The current page address and browser information are included automatically. Do not include passwords, access tokens, bank details, Social Security numbers, or protected health information.</p>
                {error && <div className="problem-error" role="alert">{error}</div>}
              </div>
              <footer><button type="button" className="btn" onClick={onClose}>Cancel</button><button type="submit" className="btn primary" disabled={busy || !subject.trim() || description.trim().length < 10}>{busy ? "Sending..." : "Submit report"}</button></footer>
            </form>
          </>
        )}
      </section>
    </div>
  );
}
'@
[IO.File]::WriteAllText($Form, $FormText, [Text.UTF8Encoding]::new($false))

$RouterText = @'
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
        raise HTTPException(status_code=503, detail="Problem report delivery is unavailable") from exc
    return {"status": "accepted", "message": "Thank you for helping us improve the website."}
'@
[IO.File]::WriteAllText($Router, $RouterText, [Text.UTF8Encoding]::new($false))

$env:FLOWFORGE_TOPBAR_PATH = $Topbar
$env:FLOWFORGE_MAIN_PATH = $Main
@'
import os
import re
from pathlib import Path

topbar_path = Path(os.environ["FLOWFORGE_TOPBAR_PATH"])
text = topbar_path.read_text(encoding="utf-8")

form_import = 'import { ProblemReportForm } from "@/components/problem-report-form";'
if form_import not in text:
    imports = list(re.finditer(r'^import .*?;\s*$', text, flags=re.MULTILINE))
    if not imports:
        raise RuntimeError("Topbar import block was not found")
    pos = imports[-1].end()
    text = text[:pos] + "\n" + form_import + text[pos:]

if "const [reportOpen, setReportOpen]" not in text:
    marker = 'const [items, setItems] = useState(notifications);'
    if marker not in text:
        raise RuntimeError("Topbar state anchor was not found")
    text = text.replace(marker, marker + '\n  const [reportOpen, setReportOpen] = useState(false);', 1)

patterns = [
    r'<button type="button" className="help-item" onClick=\{\(\) => navigate\("/support"\)\}><strong>Report an issue</strong><small>Open a local support request</small></button>',
    r'<button[^>]*>\s*<strong>Report an issue</strong>.*?</button>',
]
replacement = '<button type="button" className="help-item" onClick={() => { setMenu(null); setReportOpen(true); }}><strong>Report an issue</strong><small>Send a problem report to the FlowForge team</small></button>'
for pattern in patterns:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count:
        text = updated
        break
else:
    raise RuntimeError("Report an issue menu item was not found")

if "<ProblemReportForm" not in text:
    final = "    </header>\n  );"
    if final not in text:
        raise RuntimeError("Topbar return closing anchor was not found")
    text = text.replace(final, '      <ProblemReportForm open={reportOpen} onClose={() => setReportOpen(false)} />\n    </header>\n  );', 1)

topbar_path.write_text(text.rstrip() + "\n", encoding="utf-8")

main_path = Path(os.environ["FLOWFORGE_MAIN_PATH"])
main = main_path.read_text(encoding="utf-8")
import_line = "from flowforge.support_feedback import router as support_feedback_router"
mount_line = "app.include_router(support_feedback_router)"
if import_line not in main:
    imports = list(re.finditer(r'^from flowforge\..*?\s+import .*?$', main, flags=re.MULTILINE))
    if not imports:
        raise RuntimeError("FlowForge import block was not found")
    pos = imports[-1].end()
    main = main[:pos] + "\n" + import_line + main[pos:]
if mount_line not in main:
    mounts = list(re.finditer(r'^app\.include_router\(.*?\)\s*$', main, flags=re.MULTILINE))
    if not mounts:
        raise RuntimeError("Router mount block was not found")
    pos = mounts[-1].end()
    main = main[:pos] + "\n" + mount_line + main[pos:]
main_path.write_text(main.rstrip() + "\n", encoding="utf-8")
'@ | & $Python -
if ($LASTEXITCODE -ne 0) { throw "Problem-report integration patch failed." }

$Styles = Get-Content -LiteralPath $Css -Raw
if ($Styles -notmatch '\.problem-backdrop') {
$Styles += @'

.problem-backdrop{position:fixed;inset:0;background:#17203366;z-index:150;display:grid;place-items:center;padding:18px}.problem-dialog{width:min(720px,100%);max-height:92vh;overflow:auto;background:white;border-radius:16px;box-shadow:0 30px 90px #17203355}.problem-dialog>header{display:flex;justify-content:space-between;gap:20px;padding:22px;border-bottom:1px solid var(--line)}.problem-dialog>header small{color:var(--primary);font-size:9px;font-weight:850;letter-spacing:.1em}.problem-dialog>header h2{margin:5px 0}.problem-dialog>header p{margin:0;color:var(--muted);font-size:11px}.problem-body{padding:22px;display:grid;gap:15px}.problem-body label{display:grid;gap:6px}.problem-body label>span{font-size:10px;color:var(--muted);font-weight:750}.problem-body input,.problem-body select,.problem-body textarea{width:100%;border:1px solid var(--line);border-radius:9px;background:white;padding:11px;color:var(--text);font:inherit;resize:vertical}.problem-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.problem-dialog footer{display:flex;justify-content:flex-end;gap:8px;padding:16px 22px;border-top:1px solid var(--line)}.problem-privacy{margin:0;background:#f6f7fb;border-radius:9px;padding:11px;color:var(--muted);font-size:9px;line-height:1.55}.problem-error{background:#fff0f2;color:#a52338;padding:10px;border-radius:8px;font-size:10px}.problem-thanks{text-align:center;padding:52px 32px}.problem-thanks h2{margin:14px 0 8px}.problem-thanks p{color:var(--muted);margin:0 0 22px}.problem-check{margin:auto;width:52px;height:52px;border-radius:50%;display:grid;place-items:center;background:#e8f7ef;color:#197346;font-size:26px;font-weight:900}@media(max-width:620px){.problem-grid{grid-template-columns:1fr}.problem-backdrop{padding:8px}}
'@
}
[IO.File]::WriteAllText($Css, $Styles, [Text.UTF8Encoding]::new($false))

Push-Location $Root
try {
  & $Python -m ruff check ".\src\flowforge\support_feedback.py" ".\src\flowforge\main.py" --fix
  if ($LASTEXITCODE -ne 0) { throw "Backend Ruff validation failed." }
  & $Python -m ruff format ".\src\flowforge\support_feedback.py" ".\src\flowforge\main.py"
  if ($LASTEXITCODE -ne 0) { throw "Backend formatting failed." }
  & $Python -m py_compile ".\src\flowforge\support_feedback.py"
  if ($LASTEXITCODE -ne 0) { throw "Backend compilation failed." }
}
finally { Pop-Location }

Push-Location $Web
try {
  npm run typecheck
  if ($LASTEXITCODE -ne 0) { throw "Problem-report UI typecheck failed." }
  npm run build
  if ($LASTEXITCODE -ne 0) { throw "Problem-report UI build failed." }
}
finally { Pop-Location }

Write-Host "FLOWFORGE PROBLEM SUBMISSION INTERFACE PASSED" -ForegroundColor Green
