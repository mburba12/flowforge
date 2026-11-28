"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

import { readSession } from "@/lib/session";

import { errorText, get, list, type Row } from "./client";

export type Loaded<T> = { data: T | null; error: string; loading: boolean; reload: () => void };

/** Run an async loader on mount and whenever `key` changes; expose reload(). */
export function useLoad<T>(loader: () => Promise<T>, key: string): Loaded<T> {
  const [state, setState] = useState<{ data: T | null; error: string; loading: boolean }>({
    data: null,
    error: "",
    loading: true,
  });
  const [tick, setTick] = useState(0);
  const loaderRef = useRef(loader);
  useEffect(() => {
    loaderRef.current = loader;
  });
  useEffect(() => {
    let alive = true;
    Promise.resolve()
      .then(() => {
        if (alive) setState((s) => ({ ...s, loading: true }));
        return loaderRef.current();
      })
      .then((data) => {
        if (alive) setState({ data, error: "", loading: false });
      })
      .catch((error: unknown) => {
        if (alive) setState({ data: null, error: errorText(error), loading: false });
      });
    return () => {
      alive = false;
    };
  }, [key, tick]);
  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}

/** Rows of a business-browser resource (tenant scoped). */
export function useRows(resource: string, key = ""): Loaded<Row[]> {
  return useLoad(async () => (await list(resource)).items, `${resource}:${key}`);
}

// ------------------------------------------------------------------ permissions
let granted: Set<string> | null = null;
let pending: Promise<void> | null = null;
let forToken: string | null = null;
const listeners = new Set<() => void>();

function loadPermissions(): Promise<void> {
  if (!pending) {
    pending = get<{ permissions: string[] }>("/api/v1/me/permissions")
      .then((r) => {
        granted = new Set(r.permissions);
      })
      .catch(() => {
        granted = new Set();
      })
      .finally(() => listeners.forEach((l) => l()));
  }
  return pending;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  const token = readSession()?.accessToken ?? null;
  if (token !== forToken) {
    // A different user (or a new sign-in): never reuse another session's permissions.
    forToken = token;
    resetPermissions();
  }
  void loadPermissions();
  return () => listeners.delete(listener);
}

export function resetPermissions(): void {
  granted = null;
  pending = null;
  // Screens already showing re-read the permissions (otherwise their buttons stay
  // disabled until something new mounts, e.g. a second action in Settings).
  if (listeners.size) void loadPermissions();
}

/** Permission codes of the signed-in user (null while loading). */
export function usePermissions(): { loaded: boolean; can: (code: string) => boolean } {
  const snapshot = useSyncExternalStore(
    subscribe,
    () => granted,
    () => null,
  );
  return { loaded: snapshot !== null, can: (code: string) => Boolean(snapshot?.has(code)) };
}

/** Map of party id -> display name, for vendor/customer/worker labels. */
export function usePartyNames(key = ""): Map<string, string> {
  const parties = useRows("parties", key);
  const names = new Map<string, string>();
  for (const p of parties.data ?? []) names.set(String(p.id), String(p.display_name ?? p.party_number ?? p.id));
  return names;
}
