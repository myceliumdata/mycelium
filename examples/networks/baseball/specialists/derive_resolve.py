"""LLM derive orchestration for unaliased warehouse batting attributes (baseball pack)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from network.derive_sandbox import DeriveSourceError, run_derive_function
from network.paths import NetworkPaths
from network.warehouse import default_warehouse_path
from network.warehouse_manifest import load_warehouse_manifest

LAHMAN_PLAYER_ID = "lahman.playerID"


@dataclass(frozen=True)
class DeriveResolvedField:
    value: str
    computation_inline: str
    attribute: str
    model: str | None = None


def derive_model() -> str:
    raw = os.getenv("MYCELIUM_DERIVE_MODEL", "gpt-4o-mini").strip()
    return raw or "gpt-4o-mini"


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


def _extract_python(text: str) -> str:
    body = text.strip()
    fenced = re.search(r"```(?:python)?\s*(.*?)```", body, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        body = fenced.group(1).strip()
    return body


def generate_derive_source(
    attr: str,
    manifest: dict[str, Any],
    domain: str,
    *,
    llm_invoke: Callable[[str], str] | None = None,
) -> str:
    prompt = build_derive_prompt(attr, manifest, domain)
    if llm_invoke is not None:
        return _extract_python(llm_invoke(prompt))
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise DeriveSourceError("OPENAI_API_KEY not set for derive codegen")
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=derive_model(), temperature=0.0)
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    return _extract_python(str(content))


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


def generate_and_run_derive(
    attr: str,
    *,
    player_id: str,
    warehouse: Path,
    paths: NetworkPaths,
    manifest: dict[str, Any],
    domain: str = "batting",
    llm_invoke: Callable[[str], str] | None = None,
) -> DeriveResolvedField | None:
    if not is_derive_candidate(attr, manifest, domain):
        return None
    try:
        source = generate_derive_source(
            attr,
            manifest,
            domain,
            llm_invoke=llm_invoke,
        )
        value = run_derive_function(
            source,
            player_id=player_id,
            warehouse=warehouse,
        )
    except (DeriveSourceError, OSError, ValueError, TypeError):
        return None
    return DeriveResolvedField(
        value=value,
        computation_inline=source,
        attribute=attr.strip().lower(),
        model=derive_model() if llm_invoke is None else None,
    )
