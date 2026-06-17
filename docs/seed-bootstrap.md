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

Each row supplies values for the **bootstrap grain**'s `mvr.bind_fields`. The framework assigns uuid4 ids on import (`source=seed_bootstrap`, `validation_state=validated`). Idempotent via `bind_index`.

### Custom pack handler

Example: **`baseball`**. A module under `<network_root>/bootstrap_handlers/` implements `BootstrapHandler.run(ctx)` — warehouse ingest, multi-grain commits, external seed sources, etc. **Not** a subclass of `DefaultSeedHandler`; shares only the manifest + protocol.

## Manifest (`network.json` → `bootstrap`)

| Field | Required | Meaning |
|-------|----------|---------|
| `module` | yes | Python module path (framework `network.*` or pack `bootstrap_handlers.*`) |
| `handler` | yes | Handler class name |
| `seed_grain` | no | Entity grain for `DefaultSeedHandler` rows; must exist in `mvr.grains`. When omitted, uses `mvr.default_grain`. |

Example (CRM):

```json
"bootstrap": {
  "module": "network.bootstrap.handlers.default_seed",
  "handler": "DefaultSeedHandler",
  "seed_grain": "person"
}
```

## `seed.json` format (`rows[]`)

- Top-level object with **`rows`** array (not `people`).
- Each element is an object; keys are MVR bind field names for the bootstrap grain.
- No `id` in the file — stable ids are assigned on import.

Full bind-field validation runs at import when the network manifest is applied (`load_seed_rows`). `network create --seed` performs structural validation only (`rows[]` of objects).

## Grain selection

1. `bootstrap.seed_grain` when set in `network.json`
2. Else `mvr.default_grain`

There is no hardcoded `"person"` preference in the framework.

## Handler protocol

Handlers implement `run(ctx: BootstrapContext) -> BootstrapResult`:

- **`BootstrapContext`** — `paths`, optional `guide_text`, optional `progress`
- **`BootstrapResult`** — `entities_committed`, `sources_processed`, `handler_id`, optional `entities_by_grain`

Orchestration: `network.bootstrap.run_network_bootstrap(paths)`.

## Examples

| Network | Pattern | Handler | Seed file |
|---------|---------|---------|-----------|
| `empty-crm` | None | `DefaultSeedHandler` | absent |
| `crm` | JSON → MVR | `DefaultSeedHandler` | `rows[]` with `name`, `employer` |
| `baseball` | Custom | `LahmanSeedHandler` | Lahman zip + warehouse (see baseball README) |

## Related APIs

- `network.seed_import.load_seed_rows` — parse + validate `rows[]` against grain MVR
- `network.seed_import.import_seed_file` — import via bootstrap grain resolution
- `network.bootstrap.config.resolve_bootstrap_grain` — grain from manifest

## Source keys and field aliases (registry)

Pack handlers (e.g. Lahman) persist **namespaced source identifiers** on each `RegistryEntity`:

- **`source_keys`** — `dict[str, str]` (e.g. `{"lahman.playerID": "aaronha01"}`). Used for warehouse joins and bootstrap dedup via `lookup_by_source_key`. Not returned in default query `results[]`.
- **`source_key_index`** — persisted composite map `"lahman.playerID|aaronha01" → entity_id` (rebuilt from entities on load/save).

Two alias mechanisms — do not conflate:

| Mechanism | API | Index | Use |
|-----------|-----|-------|-----|
| **Bind alias** | `add_bind_alias` | `bind_index` only | Alternate **full** MVR bind tuple for one entity (player on multiple teams). Step-1 full MVR lookup consults `bind_index` when field-index AND misses. |
| **Field alias** | `add_field_alias` | field index only | Shared nickname on one bind field; **multiple entities** allowed (`"Dodgers"` → Brooklyn + LA) |

Field aliases live in `field_aliases` on the entity row and are merged into per-field inverted indexes at load/save. Lazy nickname expansion at query time is a separate slice.

Query-time `add_field_alias` (via `bind_alias_expansion`) persists aliases but does not yet record actor/provenance metadata — intentional v1 omission; bootstrap rows use `source="seed_bootstrap"`.

## Open vs closed identity (`identity_mode`)

Per-grain setting in `network.json` → `mvr.grains.<grain>.identity_mode`:

| Mode | Behavior |
|------|----------|
| `open` (default) | Full MVR 0-hit may return `create_pending` (CRM) |
| `closed` | No query-time entity creation; 0-hit runs lazy field alias expansion (`agents.bind_alias_expansion`) then retry lookup, suggest, or not_found |

Baseball `team` and `player` grains use `closed`. See `examples/networks/baseball/guide.md`.
