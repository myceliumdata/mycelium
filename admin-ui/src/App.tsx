import { FormEvent, useCallback, useEffect, useState } from "react";
import { fetchCapabilities, fetchHealth, fetchStatus } from "./api";
import { formatCategoryExamples, networkLabel } from "./format";
import type {
  CapabilitiesResponse,
  HealthResponse,
  StatusResponse,
} from "./types";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [capabilities, setCapabilities] = useState<CapabilitiesResponse | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [categoryFilter, setCategoryFilter] = useState("");
  const [entityInput, setEntityInput] = useState("");
  const [entityKey, setEntityKey] = useState("");

  const loadOverview = useCallback(
    async (opts?: { category?: string; entity?: string }) => {
      setLoading(true);
      setError(null);
      try {
        const [healthRes, statusRes, capsRes] = await Promise.all([
          fetchHealth(),
          fetchStatus({
            category: opts?.category || undefined,
            entity: opts?.entity || undefined,
          }),
          fetchCapabilities(),
        ]);
        setHealth(healthRes);
        setStatus(statusRes);
        setCapabilities(capsRes);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadOverview();
  }, [loadOverview]);

  const onRefresh = () => {
    void loadOverview({
      category: categoryFilter || undefined,
      entity: entityKey || undefined,
    });
  };

  const onCategorySelect = (category: string) => {
    setCategoryFilter(category);
    void loadOverview({
      category: category || undefined,
      entity: entityKey || undefined,
    });
  };

  const onEntitySubmit = (event: FormEvent) => {
    event.preventDefault();
    const key = entityInput.trim();
    setEntityKey(key);
    void loadOverview({
      category: categoryFilter || undefined,
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
        <button type="button" className="secondary" onClick={onRefresh}>
          Refresh
        </button>
      </header>

      {health?.network_root && (
        <p className="muted">network_root: {health.network_root}</p>
      )}

      {loading && <p className="muted">Loading…</p>}
      {error && <p className="error">Error: {error}</p>}

      {status && (
        <>
          <section className="card">
            <h2>Overview</h2>
            <p>
              <strong>Seed:</strong> ✅ ({status.seed_people_count})
            </p>

            {status.ontology_present && status.categories.length > 0 ? (
              <>
                <p>
                  <strong>Current ontology:</strong> ✅
                </p>
                <ul>
                  {status.categories.map((cat) => (
                    <li key={cat.name}>
                      {formatCategoryExamples(cat.name, cat.examples)}
                    </li>
                  ))}
                </ul>
              </>
            ) : (
              <p>
                <strong>Current ontology:</strong> ❌
              </p>
            )}

            {storedSpecialists.length > 0 ? (
              <>
                <p>
                  <strong>Existing specialists:</strong>
                </p>
                {storedSpecialists
                  .slice()
                  .sort((a, b) => a.category.localeCompare(b.category))
                  .map((spec) => (
                    <div className="specialist-row" key={spec.category}>
                      <span>
                        {spec.category} ({spec.record_count})
                      </span>
                      <button
                        type="button"
                        className="linkish"
                        onClick={() => onCategorySelect(spec.category)}
                      >
                        Filter
                      </button>
                    </div>
                  ))}
              </>
            ) : (
              <p>
                <strong>Existing specialists:</strong> ❌
              </p>
            )}
          </section>

          {categoryFilter && (
            <section className="card">
              <h2>Category filter: {categoryFilter}</h2>
              <button
                type="button"
                className="linkish"
                onClick={() => onCategorySelect("")}
              >
                Clear filter
              </button>
              {status.categories.length > 0 && (
                <>
                  <p className="muted">Ontology slice</p>
                  <ul>
                    {status.categories.map((cat) => (
                      <li key={cat.name}>
                        {formatCategoryExamples(cat.name, cat.examples)}
                      </li>
                    ))}
                  </ul>
                </>
              )}
              {status.specialists.length > 0 && (
                <>
                  <p className="muted">Specialists</p>
                  <ul>
                    {status.specialists
                      .slice()
                      .sort((a, b) => a.category.localeCompare(b.category))
                      .map((spec) => (
                        <li key={spec.category}>
                          {spec.category} ({spec.record_count})
                          {spec.fields_tracked.length > 0 && (
                            <span className="muted">
                              {" "}
                              — {spec.fields_tracked.length} field(s) tracked
                            </span>
                          )}
                        </li>
                      ))}
                  </ul>
                </>
              )}
            </section>
          )}

          <section className="card">
            <h2>Entity lookup</h2>
            <form className="row-actions" onSubmit={onEntitySubmit}>
              <input
                type="search"
                placeholder="Name or id"
                value={entityInput}
                onChange={(e) => setEntityInput(e.target.value)}
                aria-label="Entity key"
              />
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                aria-label="Category filter"
              >
                <option value="">All categories</option>
                {(status.categories.length > 0
                  ? status.categories
                  : ontologyCategories.map((c) => ({ name: c.name }))
                ).map((cat) => (
                  <option key={cat.name} value={cat.name}>
                    {cat.name}
                  </option>
                ))}
              </select>
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
                {status.entity_matches === 1 && status.entity_fields.length > 0 && (
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
          </section>
        </>
      )}

      {capabilities && (
        <section className="card">
          <h2>Network guide &amp; ontology</h2>
          {capabilities.guide_present && capabilities.guide ? (
            <details>
              <summary>Author guide (guide.md)</summary>
              <pre className="guide">{capabilities.guide}</pre>
            </details>
          ) : (
            <p className="muted">
              {capabilities.guide_note ?? "No guide.md for this network."}
            </p>
          )}

          {capabilities.ontology.present &&
          capabilities.ontology.categories.length > 0 ? (
            <details open>
              <summary>Category descriptions</summary>
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
        </section>
      )}
    </div>
  );
}
