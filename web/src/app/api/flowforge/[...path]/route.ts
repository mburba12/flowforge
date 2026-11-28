import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const API_BASE = (process.env.FLOWFORGE_API_BASE_URL || "http://flowforge-phase1-api-1:8000").replace(/\/$/, "");

const REPEATABLE = new Set(["GET", "HEAD", "OPTIONS", "PUT", "DELETE"]);
// Never leave the browser waiting on a stalled upstream call.
const UPSTREAM_TIMEOUT_MS = 60_000;

function isConnectionReset(error: unknown): boolean {
  const cause = (error as { cause?: { code?: string } })?.cause;
  return ["ECONNRESET", "UND_ERR_SOCKET", "EPIPE"].includes(cause?.code ?? "");
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = new URL(`${API_BASE}/${path.join("/")}`);
  target.search = request.nextUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
    redirect: "manual",
    signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
  };
  if (!['GET','HEAD'].includes(request.method)) init.body = await request.arrayBuffer();

  try {
    let upstream: Response;
    try {
      upstream = await fetch(target, { ...init, signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS) });
    } catch (error) {
      // A pooled keep-alive socket the API just closed fails with ECONNRESET before the
      // request is processed. Retry once, only for methods that are safe to repeat.
      if (!REPEATABLE.has(request.method) || !isConnectionReset(error)) throw error;
      upstream = await fetch(target, { ...init, signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS) });
    }
    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-length");
    responseHeaders.delete("transfer-encoding");
    return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch (error) {
    if (error instanceof DOMException && error.name === "TimeoutError") {
      console.error("Krov WorkAgent proxy timeout", { target: target.toString() });
      return NextResponse.json({ detail: "The Krov WorkAgent API did not answer in time. Please try again." }, { status: 504 });
    }
    console.error("Krov WorkAgent proxy failure", { target: target.toString(), error });
    return NextResponse.json({ detail: "Krov WorkAgent API is unavailable" }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;