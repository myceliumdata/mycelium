# Seed bootstrap

How network bootstrap loads initial entity rows before query-time binds. See also [architecture.md](architecture.md) § Seed bootstrap.

## Three patterns

### None (no seed fixture)

Example: **`empty-crm`**. The manifest declares `DefaultSeedHandler`, but there is **no** `seed.json` at the network root. Bootstrap commits **0** entities; growth happens from query-time binds (`create_on_deliver`, step-2 provisional rows).

### JSON → MVR (`DefaultSeedHandler`)

Example: **`crm`**. Framework handler reads `<network_root>/seed.json`:

```json
{
  "rows": [
    { "name": "Ada Lovelace", "employer": "Analytical Engines Inc" }
  ]
}
```

Each row supplies values for the **bootstrap record type**'s `mvr.bind_fields`. The framework assigns uuid4 ids on import (`source=seed_bootstrap`, `validation_state=validated`). Idempotent via `bind_index`.

### Custom pack handler

Example: **`baseball`**. A module under `<network_root>/bootstrap_handlers/` implements `BootstrapHandler.run(ctx)` — warehouse ingest, multi-record-type commits, external seed sources, etc. **Not** a subclass of `DefaultSeedHandler`; shares only the manifest + protocol.

## Manifest (`network.json` → `bootstrap`)

| Field | Required | Meaning |
|-------|----------|---------|
| `module` | yes | Python module path (framework `network.*` or pack `bootstrap_handlers.*`) |
| `handler` | yes | Handler class name |
| `seed_record_type` | no | Record type for `DefaultSeedHandler` rows; must exist in `mvr.record_types`. When omitted, uses `mvr.default_record_type`. |

Example (CRM):

```json
"bootstrap": {
  "module": "network.bootstrap.handlers.default_seed",
  "handler": "DefaultSeedHandler",
  "seed_record_type": "person"
}
```

## `seed.json` format (`rows[]`)

- Top-level object with **`rows`** array (not `people`).
- Each element is an object; keys are MVR bind field names for the bootstrap record type.
- No `id` in the file — stable ids are assigned on import.

Full bind-field validation runs at import when the network manifest is applied (`load_seed_rows`). `network create --seed` performs structural validation only (`rows[]` of objects).

## Record type selection

1. `bootstrap.seed_record_type` when set in `network.json`
2. Else `mvr.default_record_type`

There is no hardcoded `"person"` preference in the framework.

## Handler protocol

Handlers implement `run(ctx: BootstrapContext) -> BootstrapResult`:

- **`BootstrapContext`** — `paths`, optional `guide_text`, optional `progress`
- **`BootstrapResult`** — `entities_committed`, `sources_processed`, `handler_id`, optional `entities_by_record_type`

Orchestration: `network.bootstrap.run_network_bootstrap(paths)`.

## Examples

| Network | Pattern | Handler | Seed file |
|---------|---------|---------|-----------|
| `empty-crm` | None | `DefaultSeedHandler` | absent |
| `crm` | JSON → MVR | `DefaultSeedHandler` | `rows[]` with `name`, `employer` |
| `baseball` | Custom | `LahmanSeedHandler` | Lahman zip + warehouse (see baseball README) |

## Related APIs

- `network.seed_import.load_seed_rows` — parse + validate `rows[]` against record-type MVR
- `network.seed_import.import_seed_file` — import via bootstrap record-type resolution
- `network.bootstrap.config.resolve_bootstrap_record_type` — record type from manifest

## Source keys and field aliases (registry)

Pack handlers (e.g. Lahman) persist **namespaced source identifiers** on each `RegistryEntity`:

- **`source_keys`** — `dict[str, str]` (e.g. `{"lahman.playerID": "aaronha01"}`). Used for warehouse joins and bootstrap dedup via `lookup_by_source_key`. Not returned in default query `results[]`.
- **`source_key_index`** — persisted composite map `"lahman.playerID|aaronha01" → entity_id` (rebuilt from entities on load/save).

Two alias mechanisms — do not conflate:

| Mechanism | API | Index | Use |
|-----------|-----|-------|-----|
| **Bind alias** | `add_bind_alias` | `bind_index` only | Alternate **full** MVR bind tuple for one entity (e.g. CRM nickname variants). Step-1 full MVR lookup consults `bind_index` when field-index AND misses. Baseball player bootstrap commits **one** debut bind per `lahman.playerID` (no appearance-driven alias loop). |
| **Field alias** | `add_field_alias` | field index only | Shared nickname on one bind field; **multiple entities** allowed (`"Dodgers"` → Brooklyn + LA) |

Field aliases live in `field_aliases` on the entity row and are merged into per-field inverted indexes at load/save. Lazy nickname expansion at query time is a separate slice.

Query-time `add_field_alias` (via `bind_alias_expansion`) persists aliases but does not yet record actor/provenance metadata — intentional v1 omission; bootstrap rows use `source="seed_bootstrap"`.

## `new_records` policy

Per-record-type setting in `network.json` → `mvr.record_types.<name>.new_records` (required):

| Value | Behavior |
|-------|----------|
| `query_allowed` | Full MVR 0-hit may return `create_pending` (CRM). Partial 0-hit → `lookup_incomplete`. |
| `bootstrap_only` | No query-time entity creation. Partial 0-hit → `not_found` after alias expansion; full 0-hit → suggest/not_found. |

Baseball `team` and `player` record types use `bootstrap_only`. See `examples/networks/baseball/guide.md` and [query-record-type-router.md](query-record-type-router.md).
