"use client";

import { FormEvent, useState } from "react";
import { AppIcon } from "@/components/app-icon";

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
      text: "Hi, I am FlowForge AI. Ask about cash, orders, payroll, tax, inventory, or work requiring attention.",
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
        text: `I found relevant FlowForge records for "${value}". Live grounded answers and citations will appear here when the AI service is connected. This local demo is read-only.`,
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
      <button className="ai-launcher" type="button" onClick={() => setOpen(true)} aria-label="Open FlowForge AI">
        <span className="ai-spark"><AppIcon name="spark" /></span>
        <span>FlowForge AI</span>
      </button>
    );
  }

  return (
    <aside className="ai-window" aria-label="FlowForge AI chatbot">
      <div className="ai-head">
        <div><strong>FlowForge AI</strong><small>Business assistant - Demo mode</small></div>
        <button type="button" className="ai-minimize" onClick={() => setOpen(false)} aria-label="Minimize FlowForge AI">-</button>
      </div>
      <div className="ai-messages" aria-live="polite">
        {messages.map((message, index) => (
          <div className={`ai-message ${message.role}`} key={`${message.role}-${index}`}>{message.text}</div>
        ))}
      </div>
      <div className="ai-suggestions">
        {suggestions.map((suggestion) => (
          <button type="button" key={suggestion} onClick={() => send(suggestion)}>{suggestion}</button>
        ))}
      </div>
      <form className="ai-form" onSubmit={submit}>
        <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask FlowForge AI..." aria-label="Message FlowForge AI" />
        <button type="submit">Send</button>
      </form>
      <div className="ai-foot">FlowForge AI can make mistakes. Verify consequential actions.</div>
    </aside>
  );
}
