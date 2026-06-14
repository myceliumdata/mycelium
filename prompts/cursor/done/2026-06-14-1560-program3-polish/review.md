# Review — Slice 1560: Program 3 polish (P1–P4)

**Verdict:** ✅ **Approved**

**Reviewer:** Grok  
**Date:** 2026-06-14  
**CI:** `./bin/ci-local` green — **405 passed**, 26 deselected  
**Full integration:** `pytest -m full` green — **18 passed**, 413 deselected

---

## Scope check

| Item | Status |
|------|--------|
| **P1** — remove `RegistryEntity.name` / `.employer` properties | ✅ grep clean in `src/` |
| **P2** — `ensure_entity_bind_fields` requires all MVR fields | ✅ `require_full_bind_values`; `test_ensure_entity_bind_fields_requires_all_mvr_fields` |
| **P3** — fail-loud legacy `entities.json` load | ✅ `LegacyEntitiesSchemaError`; `test_legacy_entities_json_load_fails_loud` |
| **P4** — full MVR for bind_index (no `""` padding) | ✅ `require_full_bind_values` in `make_bind_key`; partial raises |
| **P5–P9** | Waived/closed per `output.md` |
| Polish doc exit criteria | ✅ checked |
| Program doc polish complete | ✅ |
| No Program 4 scope | ✅ |
| No `TODO.md` edit | ✅ |

---

## What looks good

- **`require_full_bind_values`** is the single enforcement point — used by `make_bind_key`, `_cache_values`, `ensure_entity_bind_fields`; `lookup_by_bind_values` inherits via `make_bind_key`.
- **`write_bind_fields`** skips `pop_bind_index` when entity has no prior full bind (first-write path) — avoids breaking provisional/partial rows while still requiring full MVR on assign.
- **P3** error is actionable (`refresh-example-network`) and propagates (not swallowed into empty registry).
- **Seed import** now rejects name-only rows early — aligns with P2/P4.
- **+4 smokes**, fixture ripple through `network_create` / `network_status` — expected for bind policy hardening.

---

## Why this “polish” took longer

Not cosmetic — **P1–P4 change registry invariants** that ripple:

1. **Central helper** (`require_full_bind_values`) + property removal → every `entity.name` caller + test assertions  
2. **`write_bind_fields` edge case** — first bind on partial entity (status regression test rewritten)  
3. **Seed/network-create fixtures** — name-only seed rows invalid under full MVR  
4. **4 new smokes** + updates across 6 test modules  

~200 LOC net; closer to a **small hardening slice** than doc-only polish.

---

## CI

```
./bin/ci-local — all steps passed
405 passed, 26 deselected

LANGCHAIN_TRACING_V2=false uv run pytest -m full -q
18 passed, 413 deselected
```

---

## Commit

```
chore(program3): polish registry bind_values and load hardening nits
```

**Program 3:** code + polish + gate **complete**. **Next:** Program 4 planning.