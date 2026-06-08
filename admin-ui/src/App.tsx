import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { fetchCapabilities, fetchHealth, fetchStatus } from "./api";
import { networkLabel } from "./format";
import type {
  CapabilitiesResponse,
  HealthResponse,
  StatusResponse,
} from "./types";

const POLL_MS = 3000;

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

  const storedSpecialists =
    status?.specialists.filter((spec) => spec.record_count > 0) ?? [];

  const ontologyCategories = capabilities?.ontology.categories ?? [];

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
            {status.ontology_present ? "✅" : "❌"} Categories
          </p>
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
          open={entityLookupOpen}
          onToggle={(event) => setEntityLookupOpen(event.currentTarget.open)}
        >
          <summary className="collapsible-summary disclosure-summary">
            Entity lookup
          </summary>
          <form className="row-actions" onSubmit={onEntitySubmit}>
            <input
              type="search"
              placeholder="Name or id"
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
              </p>
              {status.entity_matches === 0 && (
                <p className="empty">No seed match.</p>
              )}
              {status.entity_matches > 1 && (
                <p className="empty">
                  Multiple seed matches — narrow the key.
                </p>
              )}
              {status.entity_matches === 1 &&
                status.entity_fields.length > 0 && (
                  <table>
                    <thead>
                      <tr>
                        <th>Field</th>
                        <th>Category</th>
                        <th>Status</th>
                        <th>Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {status.entity_fields.map((field) => (
                        <tr key={field.field}>
                          <td>{field.field}</td>
                          <td>{field.category}</td>
                          <td>{field.status}</td>
                          <td>{field.value ?? "—"}</td>
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
