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
            <div className="problem-check">âœ“</div>
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
