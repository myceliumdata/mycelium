import type { LookupSuggestion } from "./types";

/** CRM placeholder until capabilities load. */
export const DEFAULT_MVR_BIND_FIELDS = ["name", "employer"] as const;

type MvrPolicyShape = {
  bind_fields?: unknown;
  default_record_type?: unknown;
  record_types?: Record<string, { bind_fields?: unknown; description?: unknown }>;
};

function asMvrPolicy(
  policy: Record<string, unknown> | undefined,
): MvrPolicyShape | null {
  const mvr = policy?.mvr;
  if (typeof mvr === "object" && mvr !== null) {
    return mvr as MvrPolicyShape;
  }
  return null;
}

function parseBindFields(raw: unknown): string[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw
    .map((item) => String(item).trim())
    .filter((item) => item.length > 0);
}

export function listRecordTypesFromPolicy(
  policy: Record<string, unknown> | undefined,
): string[] {
  const recordTypes = asMvrPolicy(policy)?.record_types;
  if (!recordTypes || typeof recordTypes !== "object") {
    return [];
  }
  return Object.keys(recordTypes).sort();
}

export function defaultRecordTypeFromPolicy(
  policy: Record<string, unknown> | undefined,
): string | null {
  const raw = asMvrPolicy(policy)?.default_record_type;
  if (typeof raw === "string" && raw.trim()) {
    return raw.trim();
  }
  return null;
}

export function mvrBindFieldsFromPolicy(
  policy: Record<string, unknown> | undefined,
  recordType?: string | null,
): string[] {
  const mvr = asMvrPolicy(policy);
  if (mvr) {
    const recordTypes = mvr.record_types;
    if (recordTypes && typeof recordTypes === "object") {
      const keys = Object.keys(recordTypes);
      const selected =
        recordType?.trim() ||
        defaultRecordTypeFromPolicy(policy) ||
        keys[0] ||
        "";
      const entry = selected ? recordTypes[selected] : undefined;
      if (entry && typeof entry === "object") {
        const fields = parseBindFields(entry.bind_fields);
        if (fields.length > 0) {
          return fields;
        }
      }
    }
    const flat = parseBindFields(mvr.bind_fields);
    if (flat.length > 0) {
      return flat;
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

  return next;
}

export function emptyLookupValues(bindFields: string[]): Record<string, string> {
  return Object.fromEntries(bindFields.map((field) => [field, ""]));
}

export type StatusFetchParams = {
  category?: string;
  id?: string;
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
      params.id = id;
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
  return Boolean(params.id) || Boolean(params.lookup);
}
