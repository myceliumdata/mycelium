# CLI — step-2 `delivery_id` network hints (A + B)

> **READY** — Claim per `prompts/cursor/WORKFLOW.md`. **Paul:** hold until baseball `ops` / warm-cache issue is resolved; then execute.

**Context:** Humans run two-step CLI queries across multiple registered networks. Step 1 often uses `--network baseball`; step 2 omits it and hits the **default** network → `not_found` with a misleading message. Deliveries are per `network_root` (`deliveries.json`), not global.

**Scope:** **CLI human UX only** — no MCP tool changes, no public JSON schema additions, no agent-facing protocol changes. Improving the step-2 `message` string in the graph is OK (humans read CLI JSON); do not add new `QueryResponse` fields.

**Design locks (Paul, June 2026):**

| Item | Decision |
|------|----------|
| A | After step-1 success, print **stderr** copy-paste command including `--network` + `delivery_id` |
| B | On step-2 deliver miss, detect `delivery_id` on **another registered network** and say so with a retry command |
| Expired on current network | Distinct message: expired TTL (~5 min), re-run step 1 on same network |
| Auto-switch network | **No** — detect and instruct only |
| Fail-fast without `--network` | **Out of scope** (optional C deferred) |

---

## A — Step-1 stderr hint (`src/main.py`)

After `run_query`, when outcome is `lookup_resolved` or `quote_required` and `response.delivery` is present:

1. Resolve the **network name** used for this invocation (same logic as `network_metadata()` in `src/network/paths.py`: CLI `--network`, registry match on root, or `network.json` `name`).
2. Print to **stderr** (not stdout JSON), one line + optional quote flag:

```text
Step 2 (same network): uv run mycelium query --network baseball --delivery-id d_abc123
```

- If only root is known (no registered name), use `--network-dir <absolute-root>` in the hint instead.
- If `quote_required`, include `--quote-id <id>` from `response.quote` in the hint.
- Do not change `QueryResponse.public_json()` / stdout JSON.

---

## B — Step-2 deliver `not_found` message

When step 2 sends `delivery_id` and `load_delivery_scope` returns not found, replace the generic:

```text
No valid delivery for delivery_id 'd_…'.
```

with a **specific** message when diagnosable.

### New helper (suggested: `src/network/delivery_hints.py`)

```python
def delivery_not_found_message(
    delivery_id: str,
    *,
    active_root: Path,
) -> str:
    ...
```

Behavior:

1. **Current network** — read `active_root/deliveries.json` (lightweight parse, no full graph):
   - Id present + **expired** → message: expired; re-run step 1 on network `<name>`.
   - Id absent → continue.
2. **Other registered networks** — `load_network_registry()` from `src/network/registry.py`; for each entry with `ok` root, check `root/deliveries.json` for the same `delivery_id` (non-expired).
   - If found exactly one other network → message:

     ```text
     No valid delivery for 'd_…' on network 'crm'.
     This delivery_id was issued on network 'baseball'.
     Retry: uv run mycelium query --network baseball --delivery-id d_…
     ```

   - Use registered **name** when available; else `--network-dir` in retry line.
3. **Fallback** — unknown or expired everywhere (same as today, slightly clearer):

   ```text
   No valid delivery for 'd_…' on network 'crm'. Re-run step 1 on the same network, then step 2 with --network <name>.
   ```

Wire into **`src/agents/dispatch.py`** only at the two `response_not_found` paths for deliver step (`load_delivery_scope` miss and hydration `ValueError`). Keep audit_log lines; update human `message` only.

**Do not** scan unregistered roots or non-registry paths (stay bounded).

---

## Tests (`@pytest.mark.smoke`)

New file `tests/test_delivery_network_hints.py`:

| Test | Assert |
|------|--------|
| `test_find_delivery_on_other_network` | Temp two roots + fake registry mapping; id on B only → hint names B |
| `test_expired_on_active_network` | Id on active root past `expires_at` → expired wording, not “other network” |
| `test_unknown_delivery_fallback` | Id nowhere → fallback message mentions re-run step 1 |
| `test_step1_hint_includes_network_name` | Unit-test a small `format_step2_cli_hint(...)` extracted from main (network name + delivery_id + optional quote_id) |

No full-graph integration required if helpers are pure.

---

## Docs (one line each)

- `README.md` — CLI two-step example: **both** steps show `--network` (if not already on both lines).
- `docs/manual-checks/2026-06-20-live-gate-program.md` — optional footnote: CLI step 2 needs same network as step 1.

---

## Scope boundaries (strict)

**May modify:**

- `src/main.py`
- `src/network/delivery_hints.py` (new)
- `src/agents/dispatch.py` (deliver-not-found messages only)
- `tests/test_delivery_network_hints.py` (new)
- `README.md` (CLI section only)

**Do not modify:**

- `TODO.md`
- `src/mycelium_mcp/server.py`
- `src/models/state.py` (no new response fields)
- `admin-ui/`
- Baseball derive / intent_map / gate-live catalogs

---

## Verification

```bash
./bin/ci-local
uv run pytest tests/test_delivery_network_hints.py -m smoke -q
```

Manual (Paul):

```bash
# Step 1
uv run mycelium query --network baseball --lookup-json '{"player":"Hank Aaron"}' --attributes ops
# stderr shows Step 2 hint with --network baseball

# Step 2 wrong (default network) — should get B message naming baseball
uv run mycelium query --delivery-id <id-from-step-1>
```

---

## Governance (mandatory)

- **Do not edit `TODO.md`.** Roadmap updates are for Grok + Paul after review.
- In `output.md`, add **"For Grok + Paul"**: what to check off, any roadmap notes.
- Cursor delivers: code, tests, task-scoped docs, and `output.md` only.

## When finished (mandatory — see WORKFLOW.md §3)

1. `./bin/ci-local` green
2. `prompts/cursor/done/2026-06-20-2000-cli-delivery-id-network-hints/` with `prompt.md` + `output.md`
3. Remove claimed file from `in-progress/` **and** ensure no duplicate remains in `next/`
4. **Do not commit or push** — tell Paul "slice ready for review"