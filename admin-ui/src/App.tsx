import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { fetchCapabilities, fetchHealth, fetchStatus, runQuery } from "./api";
import { networkLabel } from "./format";
import type {
  CapabilitiesResponse,
  HealthResponse,
  QueryResponse,
  StatusResponse,
} from "./types";

const POLL_MS = 3000;

function outcomeBadgeClass(outcome: string | null | undefined): string {
  if (!outcome) {
    return "badge neutral";
  }
  if (
    outcome === "found" ||
    outcome === "assembled" ||
    outcome === "entity_validated"
  ) {
    return "badge ok";
  }
  if (
    outcome === "quote_required" ||
    outcome === "payment_required" ||
    outcome === "principal_required"
  ) {
    return "badge metering";
  }
  if (outcome === "error" || outcome === "not_found") {
    return "badge bad";
  }
  return "badge neutral";
}

function parseAttributes(raw: string): string[] {
  return raw
    .split(/[,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(
    null,
  );
  const [initialLoading, setInitialLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);

  const [entityCategoryLimit, setEntityCategoryLimit] = useState("");
  const [entityInput, setEntityInput] = useState("");
  const [entityKey, setEntityKey] = useState("");

  const [entityLookupOpen, setEntityLookupOpen] = useState(false);
  const [guideCardOpen, setGuideCardOpen] = useState(false);
  const [queryPanelOpen, setQueryPanelOpen] = useState(false);

  const [queryEntityKey, setQueryEntityKey] = useState("");
  const [queryAttributes, setQueryAttributes] = useState("");
  const [queryEmployer, setQueryEmployer] = useState("");
  const [queryQuoteId, setQueryQuoteId] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);

  const statusInFlight = useRef(false);
  const capsInFlight = useRef(false);
  const prevOntologyPresent = useRef<boolean | null>(null);

  const statusQueryParams = useCallback(
    () => ({
      category: entityCategoryLimit || undefined,
      entity: entityKey || undefined,
    }),
    [entityCategoryLimit, entityKey],
  );

  const fetchCapabilitiesSilent = useCallback(async () => {
    if (capsInFlight.current) {
      return;
    }
    capsInFlight.current = true;
    try {
      const capsRes = await fetchCapabilities();
      setCapabilities(capsRes);
      setPollError(null);
    } catch (err) {
      setPollError(err instanceof Error ? err.message : String(err));
    } finally {
      capsInFlight.current = false;
    }
  }, []);

  const pollStatus = useCallback(async () => {
    if (statusInFlight.current || document.hidden) {
      return;
    }
    statusInFlight.current = true;
    try {
      const statusRes = await fetchStatus(statusQueryParams());
      setStatus(statusRes);
      setPollError(null);
      if (
        prevOntologyPresent.current === false &&
        statusRes.ontology_present
      ) {
        void fetchCapabilitiesSilent();
      }
      prevOntologyPresent.current = statusRes.ontology_present;
    } catch (err) {
      setPollError(err instanceof Error ? err.message : String(err));
    } finally {
      statusInFlight.current = false;
    }
  }, [fetchCapabilitiesSilent, statusQueryParams]);

  const refreshOnVisible = useCallback(async () => {
    if (statusInFlight.current || document.hidden) {
      return;
    }
    statusInFlight.current = true;
    try {
      const params = statusQueryParams();
      const [healthRes, statusRes, capsRes] = await Promise.all([
        fetchHealth(),
        fetchStatus(params),
        fetchCapabilities(),
      ]);
      setHealth(healthRes);
      setStatus(statusRes);
      setCapabilities(capsRes);
      setPollError(null);
      prevOntologyPresent.current = statusRes.ontology_present;
    } catch (err) {
      setPollError(err instanceof Error ? err.message : String(err));
    } finally {
      statusInFlight.current = false;
    }
  }, [statusQueryParams]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      setInitialLoading(true);
      setFetchError(null);
      try {
        const [healthRes, statusRes, capsRes] = await Promise.all([
          fetchHealth(),
          fetchStatus(),
          fetchCapabilities(),
        ]);
        if (cancelled) {
          return;
        }
        setHealth(healthRes);
        setStatus(statusRes);
        setCapabilities(capsRes);
        prevOntologyPresent.current = statusRes.ontology_present;
      } catch (err) {
        if (!cancelled) {
          setFetchError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) {
          setInitialLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const tick = () => {
      void pollStatus();
    };
    tick();
    const intervalId = window.setInterval(tick, POLL_MS);

    const onVisibility = () => {
      if (!document.hidden) {
        void refreshOnVisible();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [pollStatus, refreshOnVisible]);

  const fetchStatusNow = useCallback(
    async (params: { category?: string; entity?: string }) => {
      if (statusInFlight.current) {
        return;
      }
      statusInFlight.current = true;
      try {
        const statusRes = await fetchStatus(params);
        setStatus(statusRes);
        setPollError(null);
        if (
          prevOntologyPresent.current === false &&
          statusRes.ontology_present
        ) {
          void fetchCapabilitiesSilent();
        }
        prevOntologyPresent.current = statusRes.ontology_present;
      } catch (err) {
        setPollError(err instanceof Error ? err.message : String(err));
      } finally {
        statusInFlight.current = false;
      }
    },
    [fetchCapabilitiesSilent],
  );

  const onEntitySubmit = (event: FormEvent) => {
    event.preventDefault();
    const key = entityInput.trim();
    setEntityKey(key);
    void fetchStatusNow({
      category: entityCategoryLimit || undefined,
      entity: key || undefined,
    });
  };

  const runQueryRequest = useCallback(
    async (quoteIdOverride?: string) => {
      const key = queryEntityKey.trim();
      if (!key) {
        return;
      }
      setQueryLoading(true);
      setQueryError(null);
      try {
        const binding =
          queryEmployer.trim() !== ""
            ? { employer: queryEmployer.trim() }
            : undefined;
        const quoteId = (quoteIdOverride ?? queryQuoteId).trim();
        const result = await runQuery({
          entity_key: key,
          requested_attributes: parseAttributes(queryAttributes),
          binding,
          quote_id: quoteId || undefined,
        });
        setQueryResult(result);
        if (result.quote?.quote_id) {
          setQueryQuoteId(String(result.quote.quote_id));
        }
      } catch (err) {
        setQueryError(err instanceof Error ? err.message : String(err));
        setQueryResult(null);
      } finally {
        setQueryLoading(false);
      }
    },
    [queryAttributes, queryEmployer, queryEntityKey, queryQuoteId],
  );

  const onQuerySubmit = (event: FormEvent) => {
    event.preventDefault();
    void runQueryRequest();
  };

  const onAcceptQuote = () => {
    const quoteId = queryQuoteId.trim() || queryResult?.quote?.quote_id;
    if (!quoteId) {
      return;
    }
    setQueryQuoteId(String(quoteId));
    void runQueryRequest(String(quoteId));
  };

  const applySuggestion = (suggestedKey: string) => {
    setQueryEntityKey(suggestedKey);
    setEntityInput(suggestedKey);
    setEntityKey(suggestedKey);
    void fetchStatusNow({
      category: entityCategoryLimit || undefined,
      entity: suggestedKey,
    });
  };

  const storedSpecialists =
    status?.specialists.filter((spec) => spec.record_count > 0) ?? [];

  const ontologyCategories = capabilities?.ontology.categories ?? [];

  const meteringPolicy = capabilities?.policy?.metering_policy as
    | { enabled?: boolean }
    | undefined;
  const meteringEnabled = meteringPolicy?.enabled === true;

  const singleMatch =
    status?.entity_matches === 1 ? status.entity_match_summaries[0] : null;

  return (
    <div className="app">
      <header className="app-header">
        <h1>Mycelium Admin</h1>
        {health && (
          <>
            <span
              className={`badge ${health.status === "ok" ? "ok" : "bad"}`}
            >
              {health.status}
            </span>
            <span>{networkLabel(health.network_name, health.display_name)}</span>
          </>
        )}
      </header>

      {initialLoading && <p className="muted">Loading…</p>}
      {fetchError && <p className="error">Error: {fetchError}</p>}
      {pollError && !fetchError && (
        <p className="poll-error">Background refresh failed: {pollError}</p>
      )}

      {status && (
        <section className="card">
          <h2>Overview</h2>
          <p className="status-line">✅ Seed ({status.seed_people_count})</p>
          <p className="status-line">
            {status.registry_entity_count > 0 ? "✅" : "❌"} Registry (
            {status.registry_entity_count})
          </p>
          <p className="status-line">
            {status.ontology_present ? "✅" : "❌"} Categories
          </p>
          {meteringEnabled && (
            <p className="status-line muted">
              Metering enabled — attribute research may return quote_required.
            </p>
          )}
          {storedSpecialists.length > 0 ? (
            <>
              <p className="status-line">✅ Specialists</p>
              {storedSpecialists
                .slice()
                .sort((a, b) => a.category.localeCompare(b.category))
                .map((spec) => {
                  const hasStatusCounts =
                    spec.found_count > 0 ||
                    spec.pending_count > 0 ||
                    spec.na_count > 0;
                  return (
                    <details
                      key={spec.category}
                      className="specialist-details"
                    >
                      <summary className="disclosure-summary">
                        {spec.category} ({spec.record_count})
                      </summary>
                      {spec.fields_tracked.length > 0 ? (
                        <p>
                          <strong>Fields tracked:</strong>{" "}
                          {spec.fields_tracked.join(", ")}
                        </p>
                      ) : (
                        <p className="empty">No fields stored yet.</p>
                      )}
                      {hasStatusCounts && (
                        <p className="muted">
                          found {spec.found_count} · pending{" "}
                          {spec.pending_count} · n/a {spec.na_count}
                        </p>
                      )}
                    </details>
                  );
                })}
            </>
          ) : (
            <p className="status-line">❌ Specialists</p>
          )}
        </section>
      )}

      {status && (
        <details
          className="card collapsible-card"
          open={queryPanelOpen}
          onToggle={(event) => setQueryPanelOpen(event.currentTarget.open)}
        >
          <summary className="collapsible-summary disclosure-summary">
            Run query
          </summary>
          <form className="row-actions query-form" onSubmit={onQuerySubmit}>
            <input
              type="search"
              placeholder="Entity key"
              value={queryEntityKey}
              onChange={(e) => setQueryEntityKey(e.target.value)}
              aria-label="Query entity key"
            />
            <input
              type="text"
              placeholder="Attributes (email, linkedin)"
              value={queryAttributes}
              onChange={(e) => setQueryAttributes(e.target.value)}
              aria-label="Requested attributes"
            />
            <input
              type="text"
              placeholder="Binding employer (optional)"
              value={queryEmployer}
              onChange={(e) => setQueryEmployer(e.target.value)}
              aria-label="Binding employer"
            />
            <input
              type="text"
              placeholder="Quote id (retry after quote_required)"
              value={queryQuoteId}
              onChange={(e) => setQueryQuoteId(e.target.value)}
              aria-label="Quote id"
            />
            <button type="submit" disabled={queryLoading}>
              {queryLoading ? "Running…" : "Run"}
            </button>
          </form>
          {queryError && <p className="error">Query error: {queryError}</p>}
          {queryResult && (
            <div className="query-result">
              <p>
                Outcome:{" "}
                <span className={outcomeBadgeClass(queryResult.outcome)}>
                  {queryResult.outcome ?? "—"}
                </span>
              </p>
              {queryResult.required_fields.length > 0 && (
                <p>
                  <strong>Required fields:</strong>{" "}
                  {queryResult.required_fields.join(", ")}
                </p>
              )}
              {queryResult.suggestions.length > 0 && (
                <div>
                  <p>
                    <strong>Suggestions:</strong>
                  </p>
                  <ul className="suggestion-list">
                    {queryResult.suggestions.map((item) => (
                      <li key={item.id}>
                        <button
                          type="button"
                          className="link-button"
                          onClick={() => applySuggestion(item.entity_key)}
                        >
                          {item.entity_key}
                        </button>{" "}
                        <span className="muted">
                          score {item.score}
                          {item.employer ? ` · ${item.employer}` : ""}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {queryResult.message && (
                <p className="query-message">{queryResult.message}</p>
              )}
              {(queryResult.outcome === "quote_required" ||
                queryResult.outcome === "payment_required") &&
                queryResult.quote && (
                  <details className="nested-details quote-details" open>
                    <summary className="disclosure-summary">Quote</summary>
                    <p className="muted">
                      quote_id:{" "}
                      <code>{String(queryResult.quote.quote_id)}</code>
                      {queryResult.quote.total_usd != null && (
                        <>
                          {" "}
                          · total_usd {String(queryResult.quote.total_usd)}
                        </>
                      )}
                      {queryResult.quote.cache_state && (
                        <>
                          {" "}
                          · cache {String(queryResult.quote.cache_state)}
                        </>
                      )}
                    </p>
                    <pre className="query-json">
                      {JSON.stringify(queryResult.quote, null, 2)}
                    </pre>
                    {queryResult.outcome === "quote_required" && (
                      <button
                        type="button"
                        disabled={queryLoading}
                        onClick={onAcceptQuote}
                      >
                        Accept quote
                      </button>
                    )}
                    {queryResult.outcome === "payment_required" && (
                      <p className="muted">
                        Settlement required — call MCP{" "}
                        <code>pay_quote</code> with this quote_id, then retry.
                      </p>
                    )}
                  </details>
                )}
              {queryResult.results.length > 0 && (
                <pre className="query-json">
                  {JSON.stringify(queryResult.results, null, 2)}
                </pre>
              )}
            </div>
          )}
        </details>
      )}

      {status && (
        <details
          className="card collapsible-card"
          open={entityLookupOpen}
          onToggle={(event) => setEntityLookupOpen(event.currentTarget.open)}
        >
          <summary className="collapsible-summary disclosure-summary">
            Entity lookup
          </summary>
          <form className="row-actions" onSubmit={onEntitySubmit}>
            <input
              type="search"
              placeholder="Name, employer, or id"
              value={entityInput}
              onChange={(e) => setEntityInput(e.target.value)}
              aria-label="Entity key"
            />
            <label className="field-inline">
              <span className="muted">Category</span>
              <select
                value={entityCategoryLimit}
                onChange={(e) => setEntityCategoryLimit(e.target.value)}
                aria-label="Limit entity lookup to category"
              >
                <option value="">All</option>
                {(status.categories.length > 0
                  ? status.categories
                  : ontologyCategories.map((c) => ({ name: c.name }))
                ).map((cat) => (
                  <option key={cat.name} value={cat.name}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </label>
            <button type="submit">Search</button>
          </form>

          {entityKey && (
            <div>
              <p>
                Lookup: <code>{entityKey}</code> — {status.entity_matches}{" "}
                match(es)
                {status.entity_resolution_kind && (
                  <>
                    {" "}
                    ·{" "}
                    <span className="muted">
                      {status.entity_resolution_kind}
                    </span>
                  </>
                )}
              </p>
              {status.entity_required_fields.length > 0 && (
                <p>
                  <strong>Required fields:</strong>{" "}
                  {status.entity_required_fields.join(", ")}
                </p>
              )}
              {status.entity_suggestions.length > 0 && (
                <div>
                  <p>
                    <strong>Suggestions:</strong>
                  </p>
                  <ul className="suggestion-list">
                    {status.entity_suggestions.map((item) => (
                      <li key={item.id}>
                        <button
                          type="button"
                          className="link-button"
                          onClick={() => applySuggestion(item.entity_key)}
                        >
                          {item.entity_key}
                        </button>{" "}
                        <span className="muted">
                          score {item.score}
                          {item.employer ? ` · ${item.employer}` : ""}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {status.entity_matches === 0 && (
                <p className="empty">No match.</p>
              )}
              {status.entity_matches > 1 && (
                <div>
                  <p className="empty">Multiple matches — narrow the key.</p>
                  <ul className="match-list">
                    {status.entity_match_summaries.map((match) => (
                      <li key={match.id}>
                        <strong>{match.name}</strong>{" "}
                        <span className="muted">
                          {match.source}
                          {match.validation_state
                            ? ` · ${match.validation_state}`
                            : ""}
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
                  Research:{" "}
                  {singleMatch.research_allowed ? "allowed" : "gated"}
                </p>
              )}
              {status.entity_matches === 1 &&
                status.entity_fields.length > 0 && (
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
                      {status.entity_fields.map((field) => (
                        <tr key={`${field.field_kind}-${field.field}`}>
                          <td>{field.field_kind ?? "extended"}</td>
                          <td>{field.field}</td>
                          <td>{field.category}</td>
                          <td>{field.status}</td>
                          <td>{field.value ?? "—"}</td>
                          <td>{field.attr_source ?? "—"}</td>
                          <td>{field.last_researched_at ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              {status.entity_matches === 1 &&
                status.entity_fields.length === 0 && (
                  <p className="empty">
                    No specialist storage for this record yet.
                  </p>
                )}
            </div>
          )}
        </details>
      )}

      {capabilities && (
        <details
          className="card collapsible-card"
          open={guideCardOpen}
          onToggle={(event) => setGuideCardOpen(event.currentTarget.open)}
        >
          <summary className="collapsible-summary disclosure-summary">
            Network guide &amp; ontology
          </summary>
          {capabilities.guide_present && capabilities.guide ? (
            <details className="nested-details">
              <summary className="disclosure-summary">Author guide</summary>
              <pre className="guide">{capabilities.guide}</pre>
            </details>
          ) : (
            <p className="muted">
              {capabilities.guide_note ?? "No guide.md for this network."}
            </p>
          )}

          {capabilities.ontology.present &&
          capabilities.ontology.categories.length > 0 ? (
            <details className="nested-details">
              <summary className="disclosure-summary">Categories</summary>
              <ul>
                {capabilities.ontology.categories.map((cat) => (
                  <li key={cat.name}>
                    <strong>{cat.name}</strong>
                    {cat.description ? ` — ${cat.description}` : ""}
                    {cat.examples.length > 0 && (
                      <span className="muted">
                        {" "}
                        (e.g. {cat.examples.slice(0, 3).join(", ")}
                        {cat.examples.length > 3 ? ", …" : ""})
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </details>
          ) : (
            <p className="muted">{capabilities.ontology.message}</p>
          )}
        </details>
      )}
    </div>
  );
}