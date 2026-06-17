import { Fragment } from "react";
import { formatTimestamp } from "./format";
import { formatSuggestedLookup, suggestionListKey } from "./mvr";
import type {
  LookupSuggestion,
  OntologyCategory,
  QueryResponse,
  StatusResolve,
  StatusResponse,
} from "./types";

function formatStatusResolve(resolve: StatusResolve | null): string {
  if (!resolve) {
    return "—";
  }
  if (resolve.id) {
    return resolve.id;
  }
  if (resolve.lookup) {
    return Object.entries(resolve.lookup)
      .map(([field, value]) => `${field}=${value}`)
      .join(", ");
  }
  return "—";
}

function versionStatusBadgeClass(status: string): string {
  if (status === "found") {
    return "badge ok";
  }
  if (status === "na") {
    return "badge bad";
  }
  if (status === "pending") {
    return "badge metering";
  }
  return "badge neutral";
}

function formatVersionActor(actor: unknown): string {
  if (typeof actor !== "object" || actor === null) {
    return String(actor ?? "");
  }
  const typed = actor as {
    kind?: string;
    category?: string;
    specialist?: string;
  };
  return [typed.kind, typed.category, typed.specialist]
    .filter(Boolean)
    .join(" · ");
}

function versionSourceUrl(source: unknown): string {
  if (typeof source === "object" && source !== null && "url" in source) {
    return String((source as { url?: string }).url ?? "");
  }
  return String(source ?? "");
}

function VersionHistoryPanel({
  fieldName,
  versions,
}: {
  fieldName: string;
  versions: Array<Record<string, unknown>>;
}) {
  const ordered = [...versions].reverse();

  return (
    <details className="version-history">
      <summary>
        {fieldName} — {versions.length} version
        {versions.length === 1 ? "" : "s"}
      </summary>
      <ol className="version-list">
        {ordered.map((version) => {
          const status = String(version.status ?? "—");
          const sources = Array.isArray(version.sources)
            ? version.sources
                .map(versionSourceUrl)
                .filter((url) => url.length > 0)
            : [];

          return (
            <li
              key={String(version.id ?? version.at)}
              className="version-card"
            >
              <div className="version-card-header">
                <span className={versionStatusBadgeClass(status)}>
                  {status}
                </span>
                <span className="version-id">
                  {String(version.id ?? "?")}
                </span>
                <time
                  className="version-time"
                  dateTime={String(version.at ?? "")}
                >
                  {formatTimestamp(version.at)}
                </time>
              </div>
              {version.value != null && String(version.value) !== "" && (
                <p className="version-detail">
                  <span className="version-label">Value</span>
                  {String(version.value)}
                </p>
              )}
              {version.reason != null && String(version.reason) !== "" && (
                <p className="version-detail">
                  <span className="version-label">Reason</span>
                  {String(version.reason)}
                </p>
              )}
              {version.last_error != null &&
                String(version.last_error) !== "" && (
                  <p className="version-detail">
                    <span className="version-label">Error</span>
                    {String(version.last_error)}
                  </p>
                )}
              {sources.length > 0 && (
                <p className="version-detail">
                  <span className="version-label">Sources</span>
                  {sources.map((url) => (
                    <a
                      key={url}
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="version-source-link"
                    >
                      {url}
                    </a>
                  ))}
                </p>
              )}
              {version.actor != null && (
                <p className="version-detail muted">
                  {formatVersionActor(version.actor)}
                </p>
              )}
            </li>
          );
        })}
      </ol>
    </details>
  );
}

export interface EntityDrilldownProps {
  status: StatusResponse;
  label: string;
  queryResult?: QueryResponse | null;
  showCategoryFilter?: boolean;
  categoryLimit: string;
  ontologyCategories: OntologyCategory[];
  onCategoryChange: (category: string) => void;
  onApplySuggestion: (item: LookupSuggestion) => void;
}

export default function EntityDrilldown({
  status,
  label,
  queryResult = null,
  showCategoryFilter = true,
  categoryLimit,
  ontologyCategories,
  onCategoryChange,
  onApplySuggestion,
}: EntityDrilldownProps) {
  const querySuggestions = queryResult?.suggestions ?? [];
  const queryRequiredFields = queryResult?.required_fields ?? [];
  const showStatusSuggestions =
    querySuggestions.length === 0 && status.resolve_suggestions.length > 0;
  const showStatusRequiredFields =
    queryRequiredFields.length === 0 &&
    status.resolve_required_fields.length > 0;
  const singleMatch =
    status.resolve_matches === 1 ? status.resolve_match_summaries[0] : null;

  return (
    <div className="entity-drilldown">
      {showCategoryFilter && (
        <div className="row-actions">
          <label className="field-inline">
            <span className="muted">Category</span>
            <select
              value={categoryLimit}
              onChange={(event) => onCategoryChange(event.target.value)}
              aria-label="Limit entity drill-down to category"
            >
              <option value="">All</option>
              {(status.categories.length > 0
                ? status.categories
                : ontologyCategories.map((category) => ({
                    name: category.name,
                  }))
              ).map((category) => (
                <option key={category.name} value={category.name}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}
      <p>
        {label}: <code>{formatStatusResolve(status.resolve)}</code> —{" "}
        {status.resolve_matches} match(es)
        {status.resolve_kind && (
          <>
            {" "}
            ·{" "}
            <span className="muted">{status.resolve_kind}</span>
          </>
        )}
      </p>
      {showStatusRequiredFields && (
        <p>
          <strong>Required fields:</strong>{" "}
          {status.resolve_required_fields.join(", ")}
        </p>
      )}
      {showStatusSuggestions && (
        <div>
          <p>
            <strong>Suggestions:</strong>
          </p>
          <ul className="suggestion-list">
            {status.resolve_suggestions.map((item, index) => (
              <li key={suggestionListKey(item, index)}>
                <button
                  type="button"
                  className="link-button"
                  onClick={() => onApplySuggestion(item)}
                >
                  {formatSuggestedLookup(item)}
                </button>{" "}
                <span className="muted">score {item.score}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {status.resolve_matches === 0 && <p className="empty">No match.</p>}
      {status.resolve_matches > 1 && (
        <div>
          <p className="empty">Multiple matches — narrow the key.</p>
          <ul className="match-list">
            {status.resolve_match_summaries.map((match) => (
              <li key={match.id}>
                <strong>{match.name}</strong>{" "}
                <span className="muted">
                  {match.source}
                  {match.validation_state ? ` · ${match.validation_state}` : ""}
                  {match.employer ? ` · ${match.employer}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {singleMatch && (
        <p className="muted">
          Source: {singleMatch.source}
          {singleMatch.validation_state
            ? ` · ${singleMatch.validation_state}`
            : ""}
          {" · "}
          Research: {singleMatch.research_allowed ? "allowed" : "gated"}
        </p>
      )}
      {status.resolve_matches === 1 && status.entity_fields.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Kind</th>
              <th>Field</th>
              <th>Category</th>
              <th>Status</th>
              <th>Value</th>
              <th>Source</th>
              <th>Researched</th>
            </tr>
          </thead>
          <tbody>
            {status.entity_fields.map((field) => {
              const hasVersions = Boolean(field.versions?.length);
              return (
                <Fragment key={`${field.field_kind}-${field.field}`}>
                  <tr>
                    <td>{field.field_kind ?? "extended"}</td>
                    <td>{field.field}</td>
                    <td>{field.category}</td>
                    <td>{field.status}</td>
                    <td>{field.value ?? "—"}</td>
                    <td>{field.attr_source ?? "—"}</td>
                    <td>{formatTimestamp(field.last_researched_at)}</td>
                  </tr>
                  {hasVersions && field.versions && (
                    <tr className="version-history-row">
                      <td colSpan={7}>
                        <VersionHistoryPanel
                          fieldName={field.field}
                          versions={field.versions}
                        />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      )}
      {status.resolve_matches === 1 && status.entity_fields.length === 0 && (
        <p className="empty">No specialist storage for this record yet.</p>
      )}
    </div>
  );
}
