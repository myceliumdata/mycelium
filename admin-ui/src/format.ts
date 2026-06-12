/** Mirror CLI ``format_category_examples`` (slice 1200 demo layout). */
export function formatCategoryExamples(
  categoryName: string,
  examples: string[],
): string {
  if (examples.length === 0) {
    return categoryName;
  }
  if (examples.length === 1) {
    return `${categoryName} (e.g., ${examples[0]})`;
  }
  if (examples.length === 2) {
    return `${categoryName} (e.g., ${examples[0]}, ${examples[1]})`;
  }
  return `${categoryName} (e.g., ${examples[0]}, ${examples[1]}, …)`;
}

export function networkLabel(
  networkName: string | null | undefined,
  displayName: string | null | undefined,
): string {
  if (displayName && networkName && displayName !== networkName) {
    return `${networkName} — ${displayName}`;
  }
  return displayName || networkName || "network";
}

/** Human-readable timestamp for admin version history and researched-at columns. */
export function formatTimestamp(raw: unknown): string {
  if (raw == null || raw === "") {
    return "—";
  }
  const text = String(raw);
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) {
    return text;
  }
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
  });
}
