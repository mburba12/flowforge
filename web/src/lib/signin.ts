import { tokenFromResponse, writeSession } from "@/lib/session";

export type JsonObject = Record<string, unknown>;

/** Readable message from an API error body (string, validation list or {detail}). */
export function messageFrom(value: unknown, fallback: string): string {
  if (typeof value === "string" && value.trim()) return value;
  if (Array.isArray(value)) {
    const messages = value
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) return String((item as { msg: unknown }).msg).replace(/^Value error, /, "");
        return "";
      })
      .filter(Boolean);
    if (messages.length) return messages.join(" ");
  }
  if (value && typeof value === "object") {
    if ("detail" in value) return messageFrom((value as { detail: unknown }).detail, fallback);
    if ("message" in value) return messageFrom((value as { message: unknown }).message, fallback);
  }
  return fallback;
}

export async function readJson(response: Response): Promise<JsonObject> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as JsonObject;
  } catch {
    throw new Error(`Krov WorkAgent returned an invalid response (${response.status}).`);
  }
}

export function postJson(path: string, body: unknown): Promise<Response> {
  return fetch(`/api/flowforge${path}`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify(body),
  });
}

/** Store the session for a token the API just issued (after checking it with /me). */
export async function finishSignIn(payload: JsonObject): Promise<void> {
  const accessToken = tokenFromResponse(payload);
  const tokenType = typeof payload.token_type === "string" ? payload.token_type : "bearer";
  const me = await fetch("/api/flowforge/api/v1/me", { headers: { authorization: `Bearer ${accessToken}`, accept: "application/json" } });
  if (!me.ok) throw new Error(messageFrom(await readJson(me), "The account signed in, but identity verification failed."));
  const user = await readJson(me);
  const candidate = user.tenant_id ?? user.tenantId;
  writeSession({ accessToken, tokenType, tenantId: typeof candidate === "string" ? candidate : undefined, user });
}

/** Values the website passes in the address fragment (#email=…&plan=…), never sent to a server. */
export function fragmentValues(): URLSearchParams {
  if (typeof window === "undefined") return new URLSearchParams();
  return new URLSearchParams(window.location.hash.replace(/^#/, ""));
}

/** Remove the fragment so the email does not stay in the address bar or history entry. */
export function clearFragment(): void {
  if (typeof window !== "undefined" && window.location.hash) history.replaceState(null, "", window.location.pathname + window.location.search);
}
