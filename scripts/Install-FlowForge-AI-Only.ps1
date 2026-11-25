$ErrorActionPreference = "Stop"

$Root = (Get-Location).Path
$WebSrc = Join-Path $Root "web\src"
$Components = Join-Path $WebSrc "components"
$LayoutPath = Join-Path $WebSrc "app\layout.tsx"
$NavigationPath = Join-Path $WebSrc "lib\navigation.ts"
$CssPath = Join-Path $WebSrc "app\globals.css"

foreach ($Path in @($WebSrc, $Components, $LayoutPath, $NavigationPath, $CssPath)) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Run from the FlowForge project root. Missing: $Path"
    }
}

$ChatbotPath = Join-Path $Components "flowforge-ai.tsx"
$Chatbot = @'
"use client";

import { FormEvent, useState } from "react";

type Message = {
  role: "assistant" | "user";
  text: string;
};

const suggestions = [
  "What needs attention today?",
  "Summarize overdue receivables",
  "Show upcoming tax deadlines",
  "Explain reconciliation exceptions",
];

export function FlowForgeAI() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "Hi, I’m FlowForge AI. Ask about cash, orders, payroll, tax, inventory, or work requiring attention.",
    },
  ]);

  function send(text: string) {
    const value = text.trim();
    if (!value) return;

    setMessages((current) => [
      ...current,
      { role: "user", text: value },
      {
        role: "assistant",
        text: `I found relevant FlowForge records for “${value}”. Live grounded answers and citations will appear here when the AI service is connected. This local demo is read-only.`,
      },
    ]);
    setInput("");
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    send(input);
  }

  if (!open) {
    return (
      <button
        className="ai-launcher"
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open FlowForge AI"
      >
        <span className="ai-spark">✦</span>
        <span>FlowForge AI</span>
      </button>
    );
  }

  return (
    <aside className="ai-window" aria-label="FlowForge AI chatbot">
      <div className="ai-head">
        <div>
          <strong>FlowForge AI</strong>
          <small>Business assistant · Demo mode</small>
        </div>
        <button
          type="button"
          className="ai-minimize"
          onClick={() => setOpen(false)}
          aria-label="Minimize FlowForge AI"
        >
          −
        </button>
      </div>

      <div className="ai-messages" aria-live="polite">
        {messages.map((message, index) => (
          <div
            className={`ai-message ${message.role}`}
            key={`${message.role}-${index}`}
          >
            {message.text}
          </div>
        ))}
      </div>

      <div className="ai-suggestions">
        {suggestions.map((suggestion) => (
          <button
            type="button"
            key={suggestion}
            onClick={() => send(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>

      <form className="ai-form" onSubmit={submit}>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask FlowForge AI…"
          aria-label="Message FlowForge AI"
        />
        <button type="submit">Send</button>
      </form>

      <div className="ai-foot">
        AI can make mistakes. Verify consequential actions.
      </div>
    </aside>
  );
}
'@

[System.IO.File]::WriteAllText(
    $ChatbotPath,
    $Chatbot,
    [System.Text.UTF8Encoding]::new($false)
)

$Layout = Get-Content -LiteralPath $LayoutPath -Raw

if ($Layout -notmatch 'from "@/components/flowforge-ai"') {
    if ($Layout -match 'import \{Topbar\} from "@/components/topbar";') {
        $Layout = $Layout.Replace(
            'import {Topbar} from "@/components/topbar";',
            'import {Topbar} from "@/components/topbar";import {FlowForgeAI} from "@/components/flowforge-ai";'
        )
    }
    elseif ($Layout -match 'import \{ Topbar \} from "@/components/topbar";') {
        $Layout = $Layout.Replace(
            'import { Topbar } from "@/components/topbar";',
            'import { Topbar } from "@/components/topbar";`nimport { FlowForgeAI } from "@/components/flowforge-ai";'
        )
    }
    else {
        throw "Could not locate the Topbar import in layout.tsx."
    }
}

if ($Layout -notmatch '<FlowForgeAI\s*/>') {
    $Layout = $Layout.Replace("</body>", "<FlowForgeAI/></body>")
}

[System.IO.File]::WriteAllText(
    $LayoutPath,
    $Layout,
    [System.Text.UTF8Encoding]::new($false)
)

$Navigation = Get-Content -LiteralPath $NavigationPath -Raw
$Navigation = [regex]::Replace(
    $Navigation,
    '\s*\{\s*label:\s*"Copilot"\s*,\s*href:\s*"/copilot"\s*,\s*icon:\s*"✦"\s*,\s*group:\s*"Intelligence"\s*\}\s*,?',
    ""
)
[System.IO.File]::WriteAllText(
    $NavigationPath,
    $Navigation,
    [System.Text.UTF8Encoding]::new($false)
)

$Css = Get-Content -LiteralPath $CssPath -Raw
if ($Css -notmatch '\.ai-launcher\s*\{') {
$Css += @'

.ai-launcher{position:fixed;right:22px;bottom:22px;z-index:50;display:flex;align-items:center;gap:9px;border:0;border-radius:999px;background:linear-gradient(135deg,#405edb,#263b9d);color:white;padding:13px 17px;font-weight:800;box-shadow:0 14px 35px #243a9d55;cursor:pointer}
.ai-launcher:hover{transform:translateY(-1px)}
.ai-spark{font-size:18px}
.ai-window{position:fixed;right:22px;bottom:22px;width:380px;max-width:calc(100vw - 28px);height:560px;max-height:calc(100vh - 100px);z-index:55;background:white;border:1px solid var(--line);border-radius:16px;box-shadow:0 24px 70px #17203340;display:flex;flex-direction:column;overflow:hidden}
.ai-head{background:linear-gradient(135deg,#24366e,#405edb);color:white;padding:15px 16px;display:flex;align-items:center;justify-content:space-between}
.ai-head strong,.ai-head small{display:block}
.ai-head small{color:#d8e0ff;margin-top:3px;font-size:10px}
.ai-minimize{border:1px solid #ffffff3d;background:#ffffff13;color:white;width:32px;height:32px;border-radius:8px;font-size:20px;cursor:pointer}
.ai-messages{padding:14px;overflow:auto;flex:1;background:#f7f8fc}
.ai-message{max-width:85%;padding:10px 12px;border-radius:12px;margin-bottom:9px;font-size:12px;line-height:1.45}
.ai-message.assistant{background:white;border:1px solid var(--line);border-bottom-left-radius:3px}
.ai-message.user{background:#3859d7;color:white;margin-left:auto;border-bottom-right-radius:3px}
.ai-suggestions{display:flex;gap:6px;overflow:auto;padding:9px 12px;border-top:1px solid var(--line)}
.ai-suggestions button{white-space:nowrap;border:1px solid #dfe4f4;background:#f2f5ff;color:#344ca8;border-radius:999px;font-size:10px;padding:6px 9px;cursor:pointer}
.ai-form{display:flex;gap:7px;padding:11px;border-top:1px solid var(--line)}
.ai-form input{flex:1;border:1px solid var(--line);border-radius:9px;padding:10px;outline:none}
.ai-form button{border:0;background:var(--primary);color:white;border-radius:9px;padding:0 13px;font-weight:700;cursor:pointer}
.ai-foot{text-align:center;color:var(--muted);font-size:9px;padding:0 10px 9px}
@media(max-width:680px){.ai-launcher{bottom:72px;right:14px}.ai-window{right:7px;bottom:66px;width:calc(100vw - 14px);height:70vh}}
'@
}

[System.IO.File]::WriteAllText(
    $CssPath,
    $Css,
    [System.Text.UTF8Encoding]::new($false)
)

Push-Location (Join-Path $Root "web")
try {
    npm run typecheck
    if ($LASTEXITCODE -ne 0) {
        throw "FlowForge AI TypeScript validation failed."
    }

    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "FlowForge AI production build failed."
    }
}
finally {
    Pop-Location
}

Write-Host "FLOWFORGE AI-ONLY UPDATE PASSED" -ForegroundColor Green
