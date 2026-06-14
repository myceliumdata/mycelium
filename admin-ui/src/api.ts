import type {
  CapabilitiesResponse,
  HealthResponse,
  QueryResponse,
  StatusResponse,
} from "./types";

/** Empty string → same-origin relative paths (dev proxy or daemon-served SPA). */
export function apiBase(): string {
  const raw = import.meta.env.VITE_ADMIN_API_URL?.trim();
  return raw ? raw.replace(/\/$/, "") : "";
}

const MAX_ERROR_BODY = 200;

function truncateBody(text: string): string {
  const trimmed = text.trim();
  if (trimmed.length <= MAX_ERROR_BODY) {
    return trimmed;
  }
  return `${trimmed.slice(0, MAX_ERROR_BODY)}…`;
}

function looksLikeHtml(text: string, contentType: string | null): boolean {
  if (contentType?.toLowerCase().includes("text/html")) {
    return true;
  }
  const peek = text.trimStart().slice(0, 20).toLowerCase();
  return peek.startsWith("<!doctype") || peek.startsWith("<html");
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${apiBase()}${path}`;
  const response = await fetch(url, init);
  const contentType = response.headers.get("Content-Type");
  const text = await response.text();

  if (!response.ok) {
    throw new Error(
      `${response.status} ${response.statusText}: ${truncateBody(text)}`,
    );
  }

  if (looksLikeHtml(text, contentType)) {
    throw new Error(
      `Expected JSON from ${path}, got HTML — is mycelium-admin running?`,
    );
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(
      `Expected JSON from ${path}, got invalid response — is mycelium-admin running?`,
    );
  }
}

export function fetchHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>("/health");
}

export function fetchStatus(params?: {
  category?: string;
  entity?: string;
  lookup?: Record<string, string>;
}): Promise<StatusResponse> {
  const search = new URLSearchParams();
  if (params?.category) {
    search.set("category", params.category);
  }
  if (params?.entity) {
    search.set("entity", params.entity);
  }
  if (params?.lookup && Object.keys(params.lookup).length > 0) {
    search.set("lookup", JSON.stringify(params.lookup));
  }
  const query = search.toString();
  return fetchJson<StatusResponse>(query ? `/status?${query}` : "/status");
}

export function fetchCapabilities(): Promise<CapabilitiesResponse> {
  return fetchJson<CapabilitiesResponse>("/capabilities");
}

export function runQuery(body: {
  id?: string;
  lookup?: Record<string, string>;
  delivery_id?: string;
  requested_attributes?: string[];
  thread_id?: string;
  quote_id?: string;
  provenance?: boolean;
  confirm_new_entity?: boolean;
}): Promise<QueryResponse> {
  return fetchJson<QueryResponse>("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}