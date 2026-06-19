"""LLM derive orchestration for unaliased warehouse batting attributes (baseball pack)."""

from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from network.derive_sandbox import DeriveSourceError, run_derive_function
from network.paths import NetworkPaths
from network.warehouse import default_warehouse_path
from network.warehouse_manifest import load_warehouse_manifest

LAHMAN_PLAYER_ID = "lahman.playerID"
_SOURCE_TRUNCATE_CHARS = 8000


@dataclass(frozen=True)
class DeriveResolvedField:
    value: str
    computation_inline: str
    attribute: str
    model: str | None = None


@dataclass(frozen=True)
class DeriveRunResult:
    field: DeriveResolvedField | None
    audit_log: tuple[str, ...] = ()


def derive_model() -> str:
    raw = os.getenv("MYCELIUM_DERIVE_MODEL", "gpt-4o-mini").strip()
    return raw or "gpt-4o-mini"


def derive_max_attempts() -> int:
    raw = os.getenv("MYCELIUM_DERIVE_MAX_ATTEMPTS", "5").strip()
    try:
        value = int(raw)
    except ValueError:
        return 5
    return value if value > 0 else 5


def load_manifest(paths: NetworkPaths) -> dict[str, Any] | None:
    return load_warehouse_manifest(paths)


def _domain_meta(manifest: dict[str, Any], domain: str) -> dict[str, Any]:
    domains = manifest.get("domains")
    if not isinstance(domains, dict):
        return {}
    meta = domains.get(domain)
    return meta if isinstance(meta, dict) else {}


def is_derive_candidate(attr: str, manifest: dict[str, Any], domain: str) -> bool:
    key = attr.strip().lower()
    raw = _domain_meta(manifest, domain).get("derive_candidates")
    if not isinstance(raw, list):
        return False
    return key in {str(item).strip().lower() for item in raw if str(item).strip()}


def build_derive_prompt(attr: str, manifest: dict[str, Any], domain: str) -> str:
    meta = _domain_meta(manifest, domain)
    tables = meta.get("tables") or []
    grain = meta.get("grain") or []
    conventions = meta.get("conventions") or {}
    table_blocks = manifest.get("tables") if isinstance(manifest.get("tables"), dict) else {}
    columns_by_table: list[str] = []
    for table in tables:
        info = table_blocks.get(table) if isinstance(table_blocks, dict) else None
        cols = info.get("columns") if isinstance(info, dict) else []
        col_text = ", ".join(str(c) for c in cols) if isinstance(cols, list) else ""
        columns_by_table.append(f"- {table}: [{col_text}]")
    conventions_text = "\n".join(
        f"- {name}: {rule}" for name, rule in sorted(conventions.items())
    )
    return (
        "Write one Python function for a Lahman warehouse derive.\n"
        f"Attribute: {attr.strip().lower()}\n"
        f"Domain: {domain}\n"
        f"Grain: {', '.join(str(item) for item in grain)}\n"
        "Tables and columns:\n"
        f"{chr(10).join(columns_by_table) or '- (none)'}\n"
        "Conventions:\n"
        f"{conventions_text or '- (none)'}\n"
        "Rules:\n"
        "- Define exactly: def compute(player_id: str, warehouse: Path) -> str\n"
        "- Use only query_warehouse(warehouse, sql, params) and Path (already in scope).\n"
        "- No imports, no file I/O, no network, no os/subprocess.\n"
        "- Return a string value suitable for query results.\n"
        "- For batting averages use three decimal places (e.g. 0.305).\n"
        "Output only the Python function."
    )


def _truncate_source(source: str) -> str:
    if len(source) <= _SOURCE_TRUNCATE_CHARS:
        return source
    return source[:_SOURCE_TRUNCATE_CHARS] + "\n# ... truncated ..."


def build_fix_prompt(
    attr: str,
    manifest: dict[str, Any],
    domain: str,
    *,
    source: str,
    error: BaseException,
) -> str:
    return (
        "The previous derive function failed when executed.\n\n"
        f"Error: {type(error).__name__}: {error}\n\n"
        "Failed source:\n"
        "```python\n"
        f"{_truncate_source(source)}\n"
        "```\n\n"
        f"Attribute: {attr.strip().lower()}\n"
        f"Domain: {domain}\n"
        "Write a corrected compute(player_id, warehouse) function. Same rules as before.\n"
        "- Use only query_warehouse(warehouse, sql, params) and Path (already in scope).\n"
        "- No imports, no file I/O, no network, no os/subprocess.\n"
        "Output only the Python function."
    )


def _extract_python(text: str) -> str:
    body = text.strip()
    fenced = re.search(r"```(?:python)?\s*(.*?)```", body, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        body = fenced.group(1).strip()
    return body


def invoke_llm_for_prompt(
    prompt: str,
    *,
    llm_invoke: Callable[[str], str] | None = None,
) -> str:
    if llm_invoke is not None:
        return _extract_python(llm_invoke(prompt))
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise DeriveSourceError("OPENAI_API_KEY not set for derive codegen")
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=derive_model(), temperature=0.0)
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    return _extract_python(str(content))


def generate_derive_source(
    attr: str,
    manifest: dict[str, Any],
    domain: str,
    *,
    llm_invoke: Callable[[str], str] | None = None,
) -> str:
    return invoke_llm_for_prompt(
        build_derive_prompt(attr, manifest, domain),
        llm_invoke=llm_invoke,
    )


def provenance_parameters(
    *,
    player_id: str,
    paths: NetworkPaths,
    warehouse: Path | None = None,
    attribute: str,
) -> dict[str, str]:
    wh = warehouse or default_warehouse_path(paths)
    try:
        rel = str(wh.relative_to(paths.root))
    except ValueError:
        rel = str(wh)
    return {
        LAHMAN_PLAYER_ID: player_id,
        "warehouse": rel,
        "attribute": attribute.strip().lower(),
    }


def _audit_line(attr: str, message: str) -> str:
    return f"batting_specialist: derive {attr.strip().lower()} {message}"


def generate_and_run_derive(
    attr: str,
    *,
    player_id: str,
    warehouse: Path,
    paths: NetworkPaths,
    manifest: dict[str, Any],
    domain: str = "batting",
    llm_invoke: Callable[[str], str] | None = None,
) -> DeriveRunResult:
    if not is_derive_candidate(attr, manifest, domain):
        return DeriveRunResult(field=None)

    key = attr.strip().lower()
    max_attempts = derive_max_attempts()
    audit: list[str] = []
    last_source = ""
    last_error: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            if attempt == 1:
                prompt = build_derive_prompt(attr, manifest, domain)
            else:
                assert last_error is not None
                prompt = build_fix_prompt(
                    attr,
                    manifest,
                    domain,
                    source=last_source,
                    error=last_error,
                )
            source = invoke_llm_for_prompt(prompt, llm_invoke=llm_invoke)
            last_source = source
            value = run_derive_function(
                source,
                player_id=player_id,
                warehouse=warehouse,
            )
        except (DeriveSourceError, sqlite3.Error, OSError, ValueError, TypeError) as exc:
            last_error = exc
            audit.append(
                _audit_line(
                    key,
                    f"attempt {attempt} failed {type(exc).__name__}: {exc}",
                ),
            )
            continue

        audit.append(_audit_line(key, f"succeeded on attempt {attempt}"))
        return DeriveRunResult(
            field=DeriveResolvedField(
                value=value,
                computation_inline=source,
                attribute=key,
                model=derive_model() if llm_invoke is None else None,
            ),
            audit_log=tuple(audit),
        )

    audit.append(_audit_line(key, f"failed after {max_attempts} attempts"))
    return DeriveRunResult(field=None, audit_log=tuple(audit))
