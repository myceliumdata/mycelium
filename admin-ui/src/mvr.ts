import type { EntityKeySuggestion } from "./types";

/** Default CRM bind fields when capabilities are not loaded yet. */
export const DEFAULT_MVR_BIND_FIELDS = ["name", "employer"] as const;

export function mvrBindFieldsFromPolicy(
  policy: Record<string, unknown> | undefined,
): string[] {
  const mvr = policy?.mvr;
  if (mvr && typeof mvr === "object" && mvr !== null) {
    const fields = (mvr as { bind_fields?: unknown }).bind_fields;
    if (Array.isArray(fields)) {
      const cleaned = fields
        .map((item) => (typeof item === "string" ? item.trim() : ""))
        .filter(Boolean);
      if (cleaned.length > 0) {
        return cleaned;
      }
    }
  }
  return [...DEFAULT_MVR_BIND_FIELDS];
}

export function emptyLookupForBindFields(
  bindFields: string[],
  previous: Record<string, string> = {},
): Record<string, string> {
  return Object.fromEntries(
    bindFields.map((field) => [field, previous[field] ?? ""]),
  );
}

export function buildLookupPayload(
  lookup: Record<string, string>,
  bindFields: string[],
): Record<string, string> {
  const payload: Record<string, string> = {};
  for (const field of bindFields) {
    const value = lookup[field]?.trim();
    if (value) {
      payload[field] = value;
    }
  }
  return payload;
}

/** Key passed to GET /status?entity= for entity drill-down after step 1. */
export function statusEntityKeyForResolve(
  mode: "id" | "lookup",
  id: string,
  lookup: Record<string, string>,
  bindFields: string[],
): string {
  if (mode === "id") {
    return id.trim();
  }
  const byName = lookup.name?.trim();
  if (byName) {
    return byName;
  }
  for (const field of bindFields) {
    const value = lookup[field]?.trim();
    if (value) {
      return value;
    }
  }
  return "";
}

export function lookupFromSuggestion(
  item: EntityKeySuggestion,
  bindFields: string[],
  previous: Record<string, string> = {},
): Record<string, string> {
  const next = emptyLookupForBindFields(bindFields, previous);
  for (const field of bindFields) {
    if (field === "name") {
      next[field] = item.name || item.entity_key;
    } else if (field === "employer" && item.employer) {
      next[field] = item.employer;
    }
  }
  return next;
}

export function bindFieldLabel(field: string): string {
  return field
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}