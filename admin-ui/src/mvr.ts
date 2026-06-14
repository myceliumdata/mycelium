import type { LookupSuggestion } from "./types";

/** CRM default while capabilities are loading. */
export const DEFAULT_MVR_BIND_FIELDS = ["name", "employer"] as const;

export function mvrBindFieldsFromPolicy(
  policy: Record<string, unknown> | undefined,
): string[] {
  const mvr = policy?.mvr;
  if (typeof mvr === "object" && mvr !== null) {
    const raw = (mvr as { bind_fields?: unknown }).bind_fields;
    if (Array.isArray(raw)) {
      const fields = raw
        .map((item) => String(item).trim())
        .filter((item) => item.length > 0);
      if (fields.length > 0) {
        return fields;
      }
    }
  }
  return [...DEFAULT_MVR_BIND_FIELDS];
}

export function bindFieldLabel(field: string): string {
  if (!field) {
    return field;
  }
  return field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, " ");
}

export function buildLookupPayload(
  values: Record<string, string>,
  bindFields: string[],
): Record<string, string> | null {
  const lookup: Record<string, string> = {};
  for (const field of bindFields) {
    const value = values[field]?.trim();
    if (value) {
      lookup[field] = value;
    }
  }
  return Object.keys(lookup).length > 0 ? lookup : null;
}

export function statusEntityKeyForResolve(
  mode: "id" | "lookup",
  registryId: string,
  lookupValues: Record<string, string>,
  bindFields: string[],
): string | null {
  if (mode === "id") {
    const id = registryId.trim();
    return id || null;
  }
  const name = lookupValues.name?.trim();
  if (name) {
    return name;
  }
  for (const field of bindFields) {
    const value = lookupValues[field]?.trim();
    if (value) {
      return value;
    }
  }
  return null;
}

export function formatSuggestedLookup(item: LookupSuggestion): string {
  const parts = Object.entries(item.suggested_lookup ?? {})
    .filter(([, value]) => value.trim())
    .map(([field, value]) => `${field}: ${value}`);
  return parts.join(" · ") || "—";
}

export function suggestionListKey(item: LookupSuggestion, index: number): string {
  const id = item.id?.trim();
  if (id) {
    return id;
  }
  const lookupKey = JSON.stringify(item.suggested_lookup ?? {});
  return lookupKey || `suggestion-${index}`;
}

export function lookupFromSuggestion(
  item: LookupSuggestion,
  bindFields: string[],
  previous: Record<string, string>,
): Record<string, string> {
  const next = { ...previous };
  const fieldSet = new Set(bindFields);

  for (const [field, value] of Object.entries(item.suggested_lookup ?? {})) {
    if (fieldSet.has(field) && value.trim()) {
      next[field] = value.trim();
    }
  }

  for (const field of bindFields) {
    if (next[field]?.trim()) {
      continue;
    }
    const raw = (item as unknown as Record<string, unknown>)[field];
    if (raw != null && String(raw).trim()) {
      next[field] = String(raw).trim();
    }
  }

  return next;
}

export function emptyLookupValues(bindFields: string[]): Record<string, string> {
  return Object.fromEntries(bindFields.map((field) => [field, ""]));
}

export type StatusFetchParams = {
  category?: string;
  entity?: string;
  lookup?: Record<string, string>;
};

export function inspectStatusParams(
  mode: "id" | "lookup",
  registryId: string,
  lookupValues: Record<string, string>,
  bindFields: string[],
  category?: string,
): StatusFetchParams {
  const params: StatusFetchParams = {};
  if (category) {
    params.category = category;
  }
  if (mode === "id") {
    const id = registryId.trim();
    if (id) {
      params.entity = id;
    }
  } else {
    const lookup = buildLookupPayload(lookupValues, bindFields);
    if (lookup) {
      params.lookup = lookup;
    }
  }
  return params;
}

export function inspectDisplayKey(
  mode: "id" | "lookup",
  registryId: string,
  lookupValues: Record<string, string>,
  bindFields: string[],
): string | null {
  if (mode === "id") {
    const id = registryId.trim();
    return id || null;
  }
  return statusEntityKeyForResolve(mode, registryId, lookupValues, bindFields);
}

export function hasStatusTarget(params: StatusFetchParams): boolean {
  return Boolean(params.entity) || Boolean(params.lookup);
}
