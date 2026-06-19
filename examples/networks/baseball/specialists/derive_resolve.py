"""LLM derive orchestration for unaliased warehouse batting attributes (baseball pack)."""

from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from network.derive_sandbox import DeriveSourceError, run_derive_function
from network.paths import NetworkPaths
from network.warehouse import default_warehouse_path
from network.warehouse_context import domain_meta, format_warehouse_context
from network.warehouse_manifest import load_warehouse_manifest
from utils.llm_models import computation_codegen_model

LAHMAN_PLAYER_ID = "lahman.playerID"
_SOURCE_TRUNCATE_CHARS = 8000
_SANDBOX_RULES = (
    "Rules:\n"
    "- Define exactly: def compute(player_id: str, warehouse: Path) -> str\n"
    "- Use only query_warehouse(warehouse, sql, params) and Path (already in scope).\n"
    "- No imports, no file I/O, no network, no os/subprocess.\n"
    "- Return a string value suitable for query results.\n"
    "Output only the Python function."
)


class DeriveReviewRejected(ValueError):
    """Semantic review rejected a successfully executed derive result."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


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
    return domain_meta(manifest, domain)


def derive_on_miss_enabled(manifest: dict[str, Any], domain: str) -> bool:
    return bool(_domain_meta(manifest, domain).get("derive_on_miss"))


def build_derive_prompt(attr: str, manifest: dict[str, Any], domain: str) -> str:
    context = format_warehouse_context(manifest, domain)
    return (
        f"{context}\n\n"
        "Write one Python function for a Lahman warehouse derive.\n"
        f"Attribute to derive: {attr.strip().lower()}\n"
        "Infer appropriate units, aggregation, and formatting from column semantics "
        "and conventions above.\n"
        f"{_SANDBOX_RULES}"
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
    error: BaseException | None = None,
    value: str | None = None,
    review_reason: str | None = None,
) -> str:
    context = format_warehouse_context(manifest, domain)
    if review_reason is not None:
        header = (
            "The previous derive function executed but returned an implausible value.\n\n"
            f"Returned value: {value}\n"
            f"Review rejection: {review_reason}\n\n"
        )
    else:
        assert error is not None
        header = (
            "The previous derive function failed when executed.\n\n"
            f"Error: {type(error).__name__}: {error}\n\n"
        )
    return (
        f"{context}\n\n"
        f"{header}"
        "Failed source:\n"
        "```python\n"
        f"{_truncate_source(source)}\n"
        "```\n\n"
        f"Attribute to derive: {attr.strip().lower()}\n"
        "Write a corrected compute(player_id, warehouse) function.\n"
        f"{_SANDBOX_RULES}"
    )


def build_review_prompt(
    attr: str,
    manifest: dict[str, Any],
    domain: str,
    *,
    player_id: str,
    value: str,
    source: str,
) -> str:
    context = format_warehouse_context(manifest, domain)
    return (
        f"{context}\n\n"
        f"Attribute requested: {attr.strip().lower()}\n"
        f"player_id used in test run: {player_id}\n\n"
        "The following function executed without error and returned:\n"
        f"VALUE: {value}\n\n"
        "Source:\n"
        "```python\n"
        f"{_truncate_source(source)}\n"
        "```\n\n"
        "Given the warehouse context above, is VALUE a plausible answer for the requested attribute?\n\n"
        "Reply in this exact format (no code):\n"
        "VERDICT: ACCEPT\n"
        "or\n"
        "VERDICT: REJECT\n"
        "REASON: <one short paragraph>"
    )


def parse_review_verdict(text: str) -> tuple[Literal["accept", "reject"], str]:
    body = text.strip()
    if re.search(r"VERDICT:\s*ACCEPT\b", body, flags=re.IGNORECASE):
        return "accept", ""
    if re.search(r"VERDICT:\s*REJECT\b", body, flags=re.IGNORECASE):
        reason_match = re.search(r"REASON:\s*(.+)", body, flags=re.IGNORECASE | re.DOTALL)
        reason = reason_match.group(1).strip() if reason_match else "rejected without reason"
        return "reject", reason
    raise DeriveReviewRejected("unparseable review response")


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

    llm = ChatOpenAI(model=computation_codegen_model(), temperature=0.0)
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    return _extract_python(str(content))


def invoke_llm_for_review(
    prompt: str,
    *,
    review_llm_invoke: Callable[[str], str] | None = None,
) -> str:
    if review_llm_invoke is not None:
        return review_llm_invoke(prompt).strip()
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise DeriveSourceError("OPENAI_API_KEY not set for derive review")
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model=computation_codegen_model(), temperature=0.0)
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    return str(content).strip()


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
    intent_slug: str | None = None,
) -> dict[str, str]:
    wh = warehouse or default_warehouse_path(paths)
    try:
        rel = str(wh.relative_to(paths.root))
    except ValueError:
        rel = str(wh)
    params = {
        LAHMAN_PLAYER_ID: player_id,
        "warehouse": rel,
        "attribute": attribute.strip().lower(),
    }
    if intent_slug is not None:
        params["intent_slug"] = intent_slug.strip().lower()
    return params


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
    review_llm_invoke: Callable[[str], str] | None = None,
) -> DeriveRunResult:
    if not derive_on_miss_enabled(manifest, domain):
        return DeriveRunResult(field=None)

    key = attr.strip().lower()
    max_attempts = derive_max_attempts()
    audit: list[str] = []
    last_source = ""
    last_value = ""
    last_error: BaseException | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            if attempt == 1:
                prompt = build_derive_prompt(attr, manifest, domain)
            elif isinstance(last_error, DeriveReviewRejected):
                prompt = build_fix_prompt(
                    attr,
                    manifest,
                    domain,
                    source=last_source,
                    value=last_value,
                    review_reason=last_error.reason,
                )
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
            last_value = value
        except (DeriveSourceError, sqlite3.Error, OSError, ValueError, TypeError) as exc:
            if isinstance(exc, DeriveReviewRejected):
                raise
            last_error = exc
            audit.append(
                _audit_line(
                    key,
                    f"attempt {attempt} failed {type(exc).__name__}: {exc}",
                ),
            )
            continue

        try:
            review_prompt = build_review_prompt(
                attr,
                manifest,
                domain,
                player_id=player_id,
                value=value,
                source=source,
            )
            review_text = invoke_llm_for_review(
                review_prompt,
                review_llm_invoke=review_llm_invoke,
            )
            verdict, reason = parse_review_verdict(review_text)
        except DeriveReviewRejected as exc:
            last_error = exc
            audit.append(
                _audit_line(key, f"attempt {attempt} review rejected: {exc.reason}"),
            )
            continue

        if verdict == "reject":
            last_error = DeriveReviewRejected(reason or "review rejected")
            audit.append(
                _audit_line(
                    key,
                    f"attempt {attempt} review rejected: {last_error.reason}",
                ),
            )
            continue

        audit.append(_audit_line(key, f"succeeded on attempt {attempt}"))
        return DeriveRunResult(
            field=DeriveResolvedField(
                value=value,
                computation_inline=source,
                attribute=key,
                model=computation_codegen_model() if llm_invoke is None else None,
            ),
            audit_log=tuple(audit),
        )

    audit.append(_audit_line(key, f"failed after {max_attempts} attempts"))
    return DeriveRunResult(field=None, audit_log=tuple(audit))
