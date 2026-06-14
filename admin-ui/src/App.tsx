import {
  FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { fetchCapabilities, fetchHealth, fetchStatus, runQuery } from "./api";
import EntityDrilldown from "./EntityDrilldown";
import { networkLabel } from "./format";
import ResolveForm from "./ResolveForm";
import {
  buildLookupPayload,
  emptyLookupValues,
  hasStatusTarget,
  inspectDisplayKey,
  inspectStatusParams,
  lookupFromSuggestion,
  mvrBindFieldsFromPolicy,
  type StatusFetchParams,
} from "./mvr";
import type {
  CapabilitiesResponse,
  EntityKeySuggestion,
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
    outcome === "entity_validated" ||
    outcome === "lookup_resolved"
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
  if (
    outcome === "lookup_incomplete" ||
    outcome === "lookup_suggested"
  ) {
    return "badge negotiation";
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
  const [statusParams, setStatusParams] = useState<StatusFetchParams>({});
  const [lastInspectKey, setLastInspectKey] = useState<string | null>(null);
  const [queryDrilldownActive, setQueryDrilldownActive] = useState(false);

  const [entityLookupPanelOpen, setEntityLookupPanelOpen] = useState(false);
  const [guideCardOpen, setGuideCardOpen] = useState(false);
  const [queryPanelOpen, setQueryPanelOpen] = useState(false);

  const [resolveMode, setResolveMode] = useState<"id" | "lookup">("lookup");
  const [queryRegistryId, setQueryRegistryId] = useState("");
  const [lookupValues, setLookupValues] = useState<Record<string, string>>({});
  const [queryAttributes, setQueryAttributes] = useState("");
  const [queryDeliveryId, setQueryDeliveryId] = useState("");
  const [queryQuoteId, setQueryQuoteId] = useState("");
  const [queryConfirmNewEntity, setQueryConfirmNewEntity] = useState(false);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);

  const bindFields = mvrBindFieldsFromPolicy(capabilities?.policy);
  const step2Active = queryDeliveryId.trim().length > 0;

  const statusInFlight = useRef(false);
  const capsInFlight = useRef(false);
  const prevOntologyPresent = useRef<boolean | null>(null);

  const statusQueryParams = useCallback((): StatusFetchParams => {
    if (lastInspectKey || queryDrilldownActive) {
      return {
        ...statusParams,
        category: entityCategoryLimit || undefined,
      };
    }
    return {};
  }, [
    entityCategoryLimit,
    lastInspectKey,
    queryDrilldownActive,
    statusParams,
  ]);

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

  useEffect(() => {
    setLookupValues((previous) => {
      const next = emptyLookupValues(bindFields);
      for (const field of bindFields) {
        if (previous[field] != null) {
          next[field] = previous[field];
        }
      }
      return next;
    });
  }, [bindFields.join("|")]);

  const fetchStatusNow = useCallback(
    async (params: StatusFetchParams) => {
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

  const onResolveModeChange = (mode: "id" | "lookup") => {
    setResolveMode(mode);
    if (mode === "id") {
      setLookupValues(emptyLookupValues(bindFields));
      setQueryConfirmNewEntity(false);
    } else {
      setQueryRegistryId("");
    }
  };

  const onLookupFieldChange = (field: string, value: string) => {
    setLookupValues((previous) => ({ ...previous, [field]: value }));
  };

  const onCategoryLimitChange = (category: string) => {
    setEntityCategoryLimit(category);
    const next = {
      ...statusParams,
      category: category || undefined,
    };
    setStatusParams(next);
    if (lastInspectKey || queryDrilldownActive) {
      void fetchStatusNow(next);
    }
  };

  const refreshInspectFromForm = useCallback(
    (
      mode: "id" | "lookup",
      registryId: string,
      values: Record<string, string>,
    ) => {
      const params = inspectStatusParams(
        mode,
        registryId,
        values,
        bindFields,
        entityCategoryLimit || undefined,
      );
      if (!hasStatusTarget(params)) {
        return;
      }
      const label = inspectDisplayKey(mode, registryId, values, bindFields);
      setStatusParams(params);
      setLastInspectKey(label);
      setQueryDrilldownActive(false);
      void fetchStatusNow(params);
    },
    [bindFields, entityCategoryLimit, fetchStatusNow],
  );

  const onInspect = () => {
    refreshInspectFromForm(resolveMode, queryRegistryId, lookupValues);
  };

  const refreshQueryDrilldownWith = useCallback(
    (
      mode: "id" | "lookup",
      registryId: string,
      values: Record<string, string>,
    ) => {
      const params = inspectStatusParams(
        mode,
        registryId,
        values,
        bindFields,
        entityCategoryLimit || undefined,
      );
      if (!hasStatusTarget(params)) {
        return;
      }
      setStatusParams(params);
      setQueryDrilldownActive(true);
      void fetchStatusNow(params);
    },
    [bindFields, entityCategoryLimit, fetchStatusNow],
  );

  const refreshQueryDrilldown = useCallback(() => {
    refreshQueryDrilldownWith(resolveMode, queryRegistryId, lookupValues);
  }, [
    lookupValues,
    queryRegistryId,
    refreshQueryDrilldownWith,
    resolveMode,
  ]);

  const runQueryStep1 = useCallback(async () => {
    const attrs = parseAttributes(queryAttributes);
    let body: Parameters<typeof runQuery>[0];

    if (resolveMode === "id") {
      const id = queryRegistryId.trim();
      if (!id) {
        return;
      }
      body = {
        id,
        requested_attributes: attrs.length > 0 ? attrs : undefined,
      };
    } else {
      const lookup = buildLookupPayload(lookupValues, bindFields);
      if (!lookup) {
        return;
      }
      body = {
        lookup,
        requested_attributes: attrs.length > 0 ? attrs : undefined,
        confirm_new_entity: queryConfirmNewEntity || undefined,
      };
    }

    setQueryLoading(true);
    setQueryError(null);
    try {
      const result = await runQuery(body);
      setQueryResult(result);

      if (result.delivery?.delivery_id) {
        setQueryDeliveryId(String(result.delivery.delivery_id));
        setLookupValues(emptyLookupValues(bindFields));
        setQueryRegistryId("");
        setQueryAttributes("");
      }
      if (
        result.quote?.quote_id &&
        (result.outcome === "quote_required" ||
          result.outcome === "payment_required")
      ) {
        setQueryQuoteId(String(result.quote.quote_id));
      }

      refreshQueryDrilldown();
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : String(err));
      setQueryResult(null);
      setQueryDrilldownActive(false);
    } finally {
      setQueryLoading(false);
    }
  }, [
    bindFields,
    lookupValues,
    queryAttributes,
    queryConfirmNewEntity,
    queryRegistryId,
    refreshQueryDrilldown,
    resolveMode,
  ]);

  const runQueryStep2 = useCallback(
    async (quoteIdOverride?: string) => {
      const deliveryId = queryDeliveryId.trim();
      if (!deliveryId) {
        return;
      }
      const quoteId = (quoteIdOverride ?? queryQuoteId).trim();
      const body: Parameters<typeof runQuery>[0] = quoteId
        ? { delivery_id: deliveryId, quote_id: quoteId }
        : { delivery_id: deliveryId };

      setQueryLoading(true);
      setQueryError(null);
      try {
        const result = await runQuery(body);
        setQueryResult(result);

        const terminalOutcome =
          result.outcome === "found" ||
          result.outcome === "assembled" ||
          result.outcome === "entity_validated";

        if (terminalOutcome) {
          setQueryDeliveryId("");
          setQueryQuoteId("");
          setQueryDrilldownActive(false);
        }
        if (
          result.quote?.quote_id &&
          (result.outcome === "quote_required" ||
            result.outcome === "payment_required")
        ) {
          setQueryQuoteId(String(result.quote.quote_id));
        }
      } catch (err) {
        setQueryError(err instanceof Error ? err.message : String(err));
        setQueryResult(null);
      } finally {
        setQueryLoading(false);
      }
    },
    [queryDeliveryId, queryQuoteId],
  );

  const onAcceptQuote = () => {
    const quoteId = queryQuoteId.trim() || queryResult?.quote?.quote_id;
    if (!quoteId) {
      return;
    }
    setQueryQuoteId(String(quoteId));
    void runQueryStep2(String(quoteId));
  };

  const applySuggestion = (item: EntityKeySuggestion) => {
    const nextLookup = lookupFromSuggestion(item, bindFields, lookupValues);
    setResolveMode("lookup");
    setQueryRegistryId("");
    setLookupValues(nextLookup);
    setQueryConfirmNewEntity(false);

    if (queryDrilldownActive) {
      refreshQueryDrilldownWith("lookup", "", nextLookup);
    } else if (lastInspectKey) {
      refreshInspectFromForm("lookup", "", nextLookup);
    }
  };

  const onDeliverSubmit = (event: FormEvent) => {
    event.preventDefault();
    void runQueryStep2();
  };

  const storedSpecialists =
    status?.specialists.filter((spec) => spec.record_count > 0) ?? [];

  const ontologyCategories = capabilities?.ontology.categories ?? [];

  const meteringPolicy = capabilities?.policy?.metering_policy as
    | { enabled?: boolean }
    | undefined;
  const meteringEnabled = meteringPolicy?.enabled === true;

  const resolveFormProps = {
    bindFields,
    mode: resolveMode,
    registryId: queryRegistryId,
    lookupValues,
    onModeChange: onResolveModeChange,
    onRegistryIdChange: setQueryRegistryId,
    onLookupFieldChange,
  };

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
          <p className="status-line">
            {status.registry_entity_count > 0 ? "✅" : "❌"} Entities (
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
          open={entityLookupPanelOpen}
          onToggle={(event) =>
            setEntityLookupPanelOpen(event.currentTarget.open)
          }
        >
          <summary className="collapsible-summary disclosure-summary">
            Entity lookup
          </summary>
          <p className="step-helper muted">
            Read-only inspect via <code>GET /status</code> — no{" "}
            <code>POST /query</code>. Bind fields: {bindFields.join(", ")}.
          </p>
          <ResolveForm
            {...resolveFormProps}
            radioName="resolve-mode-inspect"
          />
          <div className="panel-actions">
            <button type="button" onClick={onInspect}>
              Inspect
            </button>
          </div>
          {lastInspectKey && (
            <EntityDrilldown
              status={status}
              label="Lookup"
              categoryLimit={entityCategoryLimit}
              ontologyCategories={ontologyCategories}
              onCategoryChange={onCategoryLimitChange}
              onApplySuggestion={applySuggestion}
            />
          )}
        </details>
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
          <div className="query-form">
            <ResolveForm
              {...resolveFormProps}
              disabled={step2Active || queryLoading}
              radioName="resolve-mode-query"
            />
            <div className="query-step-extras">
              <label className="attributes-field">
                <span className="muted">Requested attributes</span>
                <input
                  type="search"
                  placeholder="email, linkedin"
                  value={queryAttributes}
                  onChange={(event) => setQueryAttributes(event.target.value)}
                  aria-label="Requested attributes"
                  disabled={step2Active || queryLoading}
                />
              </label>
              {queryResult?.outcome === "lookup_suggested" &&
                !step2Active &&
                resolveMode === "lookup" && (
                  <label className="confirm-new-entity">
                    <input
                      type="checkbox"
                      checked={queryConfirmNewEntity}
                      onChange={(event) =>
                        setQueryConfirmNewEntity(event.target.checked)
                      }
                    />
                    Confirm new entity (ignore suggestions)
                  </label>
                )}
            </div>
            <div className="panel-actions">
              <button
                type="button"
                disabled={queryLoading || step2Active}
                onClick={() => void runQueryStep1()}
              >
                {queryLoading ? "Running…" : "Run"}
              </button>
            </div>
            {queryError && <p className="error">Query error: {queryError}</p>}
            {queryResult && (
              <div className="query-result">
                <p>
                  Outcome:{" "}
                  <span className={outcomeBadgeClass(queryResult.outcome)}>
                    {queryResult.outcome ?? "—"}
                  </span>
                </p>
                {queryResult.total_matches != null && (
                  <p className="muted">
                    total_matches: {queryResult.total_matches}
                    {queryResult.delivery?.create_on_deliver === true
                      ? " (full MVR)"
                      : ""}
                  </p>
                )}
                {queryResult.delivery?.delivery_id &&
                  (queryResult.outcome === "lookup_resolved" ||
                    queryResult.outcome === "quote_required" ||
                    queryResult.outcome === "payment_required") && (
                    <p className="muted">
                      delivery_id:{" "}
                      <code>{String(queryResult.delivery.delivery_id)}</code>
                      {" · "}
                      Use Deliver below for step 2.
                    </p>
                  )}
                {(queryResult.required_fields ?? []).length > 0 && (
                  <p>
                    <strong>Required fields:</strong>{" "}
                    {(queryResult.required_fields ?? []).join(", ")}
                  </p>
                )}
                {(queryResult.suggestions ?? []).length > 0 && (
                  <div>
                    <p>
                      <strong>Suggestions:</strong>
                    </p>
                    <ul className="suggestion-list">
                      {(queryResult.suggestions ?? []).map((item) => (
                        <li key={item.id}>
                          <button
                            type="button"
                            className="link-button"
                            onClick={() => applySuggestion(item)}
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
            {queryDrilldownActive && queryResult && (
              <EntityDrilldown
                status={status}
                label="Drill-down"
                queryResult={queryResult}
                showCategoryFilter={false}
                categoryLimit={entityCategoryLimit}
                ontologyCategories={ontologyCategories}
                onCategoryChange={onCategoryLimitChange}
                onApplySuggestion={applySuggestion}
              />
            )}
            <form className="deliver-form" onSubmit={onDeliverSubmit}>
              <fieldset className="query-step-fieldset">
                <legend>Step 2 — deliver</legend>
                <div className="deliver-fields">
                  <input
                    type="search"
                    placeholder="Delivery id (from step 1)"
                    value={queryDeliveryId}
                    onChange={(event) =>
                      setQueryDeliveryId(event.target.value)
                    }
                    aria-label="Delivery id"
                  />
                  <input
                    type="search"
                    placeholder="Quote id (retry after quote_required)"
                    value={queryQuoteId}
                    onChange={(event) => setQueryQuoteId(event.target.value)}
                    aria-label="Quote id"
                  />
                  <button type="submit" disabled={queryLoading}>
                    {queryLoading ? "Delivering…" : "Deliver"}
                  </button>
                </div>
              </fieldset>
            </form>
          </div>
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