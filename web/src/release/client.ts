"use client";

import { clearSession, readSession } from "@/lib/session";

/** Typed client for the FlowForge API through the web proxy (/api/flowforge). */

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export type Params = Record<string, string | number | boolean | undefined | null>;
export type Page<T> = { resource?: string; total: number; items: T[] };
export type Row = Record<string, unknown>;

function describe(detail: unknown, status: number): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const loc = "loc" in item && Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
          return loc ? `${loc}: ${String(item.msg)}` : String(item.msg);
        }
        return typeof item === "string" ? item : "";
      })
      .filter(Boolean);
    if (parts.length) return parts.join("; ");
  }
  if (status === 403) return "You do not have permission for this action.";
  return `Request failed (HTTP ${status}).`;
}

function query(params?: Params): string {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export async function request<T>(method: string, path: string, body?: unknown, params?: Params): Promise<T> {
  const headers = new Headers({ accept: "application/json" });
  const session = readSession();
  if (session?.accessToken) headers.set("authorization", `Bearer ${session.accessToken}`);
  if (body !== undefined) headers.set("content-type", "application/json");
  const response = await fetch(`/api/flowforge${path}${query(params)}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  const type = response.headers.get("content-type") ?? "";
  const payload: unknown = response.status === 204 ? null : type.includes("json") ? await response.json() : await response.text();
  if (response.status === 401 && typeof window !== "undefined") {
    clearSession();
    if (!window.location.pathname.startsWith("/login")) window.location.assign("/login");
  }
  if (!response.ok) {
    const detail = payload && typeof payload === "object" && "detail" in payload ? (payload as { detail: unknown }).detail : payload;
    throw new ApiError(response.status, describe(detail, response.status));
  }
  return payload as T;
}

function authHeaders(): Headers {
  const headers = new Headers({ accept: "application/json" });
  const session = readSession();
  if (session?.accessToken) headers.set("authorization", `Bearer ${session.accessToken}`);
  return headers;
}

/** Multipart upload (files plus form fields); the browser sets the content type. */
export async function upload<T>(path: string, form: FormData): Promise<T> {
  const response = await fetch(`/api/flowforge${path}`, { method: "POST", headers: authHeaders(), body: form, cache: "no-store" });
  const type = response.headers.get("content-type") ?? "";
  const payload: unknown = type.includes("json") ? await response.json() : await response.text();
  if (response.status === 401 && typeof window !== "undefined") {
    clearSession();
    window.location.href = "/login";
  }
  if (!response.ok) {
    const detail = payload && typeof payload === "object" && "detail" in payload ? (payload as { detail: unknown }).detail : payload;
    throw new ApiError(response.status, describe(detail, response.status));
  }
  return payload as T;
}

/** Open (PDF, images) or save a stored file; the API needs the sign-in token, so fetch it. */
export async function openFile(path: string, filename: string, inline: boolean): Promise<void> {
  const response = await fetch(`/api/flowforge${path}`, { headers: authHeaders(), cache: "no-store" });
  if (!response.ok) throw new ApiError(response.status, describe(null, response.status));
  const url = URL.createObjectURL(await response.blob());
  if (inline) {
    window.open(url, "_blank", "noopener");
  } else {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
  }
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

export const get = <T>(path: string, params?: Params) => request<T>("GET", path, undefined, params);
export const post = <T>(path: string, body?: unknown, params?: Params) => request<T>("POST", path, body ?? undefined, params);
export const put = <T>(path: string, body: unknown) => request<T>("PUT", path, body);
export const patch = <T>(path: string, body: unknown) => request<T>("PATCH", path, body);
export const del = <T>(path: string) => request<T>("DELETE", path);

/** Tenant-scoped record list through the read-only business browser (max 200 rows). */
export function list<T = Row>(resource: string, filter?: { field: string; value: string }): Promise<Page<T>> {
  return get<Page<T>>(`/api/v1/business/${resource}`, { limit: 200, ...(filter ?? {}) });
}

export const today = () => new Date().toISOString().slice(0, 10);

export function money(value: unknown): string {
  const n = typeof value === "number" ? value : Number(value ?? 0);
  if (!Number.isFinite(n)) return String(value ?? "");
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
