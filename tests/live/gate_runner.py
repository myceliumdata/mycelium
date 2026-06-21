"""Live gate scenario runner — YAML catalogs + in-process run_query."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agents.classification import reset_category_tree
from agents.entity_registry import get_entity_registry, reset_entity_registry
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import reset_agent_registry
from graphs.core import reset_core_graph, run_query
from models.state import EntityQuery
from network.delivery import reset_delivery_store
from network.paths import NetworkPaths, apply_network_paths
from storage.core import reset_storage

from assertions import (
    check_assertions,
    extract_provenance_timestamp,
    missing_env_vars,
)

LIVE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LIVE_DIR.parent.parent

_TEMPLATE_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
RATE_DRIFT_ATTRS = frozenset({
    "career_avg",
    "career_era",
    "pitcher_career_era",
    "ops",
    "career_whip",
    "k_per_9",
    "whip",
    "fielding_percentage",
    "pitcher_career_whip",
    "pitcher_k_per_9",
})


def rate_value_drift(
    expected: Any,
    actual: Any,
    *,
    tolerance: float = 0.001,
) -> bool:
    """Return True when float rate stats differ beyond tolerance."""
    try:
        return abs(float(actual) - float(expected)) > tolerance
    except (TypeError, ValueError):
        return True


@dataclass
class NetworkEntry:
    name: str
    catalog_path: Path
    anchors_path: Path | None
    default_root: Path
    phases: list[str]
    refresh_before_gate: bool = False
    fresh_derive_before_gate: bool = False


@dataclass
class ScenarioSpec:
    id: str
    phase: str
    description: str
    skip_if_missing_env: list[str] = field(default_factory=list)
    depends_on: str | None = None
    skip_query: bool = False
    step1: dict[str, Any] = field(default_factory=dict)
    assert_step1: dict[str, Any] = field(default_factory=dict)
    step2: dict[str, Any] | bool | None = None
    assert_step2: dict[str, Any] = field(default_factory=dict)
    capture: dict[str, str] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    id: str
    phase: str
    passed: bool
    skipped: bool
    detail: str
    request: dict[str, Any] | None = None
    response: dict[str, Any] | None = None


def expand_path(path_str: str) -> Path:
    return Path(os.path.expanduser(path_str)).resolve()


def load_networks_registry(path: Path | None = None) -> dict[str, NetworkEntry]:
    registry_path = path or (LIVE_DIR / "networks.yaml")
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    entries: dict[str, NetworkEntry] = {}
    for name, cfg in raw.items():
        catalog = LIVE_DIR / str(cfg["catalog"])
        anchors_raw = cfg.get("anchors")
        anchors = LIVE_DIR / str(anchors_raw) if anchors_raw else None
        entries[name] = NetworkEntry(
            name=name,
            catalog_path=catalog,
            anchors_path=anchors,
            default_root=expand_path(str(cfg["default_root"])),
            phases=list(cfg.get("phases") or []),
            refresh_before_gate=bool(cfg.get("refresh_before_gate", False)),
            fresh_derive_before_gate=bool(cfg.get("fresh_derive_before_gate", False)),
        )
    return entries


def load_anchors(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_anchor_expr(expr: str, *, anchors: dict[str, Any]) -> Any:
    node: Any = anchors
    for part in expr.split(".")[1:]:
        node = node[part]
    return node


def _resolve_context_expr(expr: str, *, context: dict[str, Any]) -> Any:
    node: Any = context
    for part in expr.split(".")[1:]:
        node = node[part]
    if node is None:
        return ""
    return node


def _resolve_template(value: Any, *, anchors: dict[str, Any], context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        whole = _TEMPLATE_RE.fullmatch(value.strip())
        if whole is not None:
            expr = whole.group(1).strip()
            if expr.startswith("anchors."):
                return _resolve_anchor_expr(expr, anchors=anchors)
            if expr.startswith("context."):
                return _resolve_context_expr(expr, context=context)
            raise KeyError(f"unknown template: {expr}")

        def repl(match: re.Match[str]) -> str:
            expr = match.group(1).strip()
            if expr.startswith("anchors."):
                return str(_resolve_anchor_expr(expr, anchors=anchors))
            if expr.startswith("context."):
                return str(_resolve_context_expr(expr, context=context))
            raise KeyError(f"unknown template: {expr}")

        if "{{" in value:
            return _TEMPLATE_RE.sub(repl, value)
        return value
    if isinstance(value, dict):
        return {
            key: _resolve_template(item, anchors=anchors, context=context)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _resolve_template(item, anchors=anchors, context=context) for item in value
        ]
    return value


def load_catalog(path: Path) -> list[ScenarioSpec]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    scenarios: list[ScenarioSpec] = []
    for item in raw.get("scenarios") or []:
        scenarios.append(
            ScenarioSpec(
                id=str(item["id"]),
                phase=str(item["phase"]),
                description=str(item.get("description") or item["id"]),
                skip_if_missing_env=list(item.get("skip_if_missing_env") or []),
                depends_on=item.get("depends_on"),
                skip_query=bool(item.get("skip_query")),
                step1=dict(item.get("step1") or {}),
                assert_step1=dict(item.get("assert_step1") or {}),
                step2=item.get("step2"),
                assert_step2=dict(item.get("assert_step2") or {}),
                capture=dict(item.get("capture") or {}),
            ),
        )
    return scenarios


def filter_scenarios(
    scenarios: list[ScenarioSpec],
    *,
    phases: set[str] | None,
) -> list[ScenarioSpec]:
    if not phases:
        return scenarios
    return [scenario for scenario in scenarios if scenario.phase in phases]


def reset_query_runtime() -> None:
    for reset_fn in (
        reset_storage,
        reset_entity_registry,
        reset_core_graph,
        reset_category_tree,
        reset_delivery_store,
        reset_agent_registry,
        reset_agent_factory,
    ):
        reset_fn()


def _public_dict(response: Any) -> dict[str, Any]:
    return response.public_dict()


def _build_query(payload: dict[str, Any]) -> EntityQuery:
    return EntityQuery.model_validate(payload)


def _invalid_query_result(
    spec: ScenarioSpec,
    *,
    detail: str,
    request: dict[str, Any],
) -> ScenarioResult:
    return ScenarioResult(
        id=spec.id,
        phase=spec.phase,
        passed=False,
        skipped=False,
        detail=detail,
        request=request,
    )


def run_scenario(
    spec: ScenarioSpec,
    *,
    anchors: dict[str, Any],
    context: dict[str, Any],
) -> ScenarioResult:
    missing = missing_env_vars(spec.skip_if_missing_env)
    if missing:
        return ScenarioResult(
            id=spec.id,
            phase=spec.phase,
            passed=True,
            skipped=True,
            detail=f"skipped (missing env: {', '.join(missing)})",
        )

    if spec.depends_on and spec.depends_on not in context:
        return ScenarioResult(
            id=spec.id,
            phase=spec.phase,
            passed=False,
            skipped=False,
            detail=f"depends_on {spec.depends_on!r} not satisfied",
        )

    if spec.skip_query:
        public1: dict[str, Any] = {}
        response1 = None
        step1_payload = {}
    else:
        step1_payload = _resolve_template(spec.step1, anchors=anchors, context=context)
        try:
            query1 = _build_query(step1_payload)
        except ValidationError as exc:
            return _invalid_query_result(
                spec,
                detail=f"invalid step1 query: {exc}",
                request=step1_payload,
            )
        response1 = run_query(query1)
        public1 = _public_dict(response1)

    failures = check_assertions(
        response1,
        public=public1,
        assertions=_resolve_template(spec.assert_step1, anchors=anchors, context=context),
        context=context,
        network_root=context.get("_network_root"),
    )
    if failures:
        return ScenarioResult(
            id=spec.id,
            phase=spec.phase,
            passed=False,
            skipped=False,
            detail="; ".join(failures),
            request=step1_payload,
            response=public1,
        )

    scenario_ctx: dict[str, Any] = {
        "delivery_id": None,
        "quote_id": None,
        "outcome": None,
    }
    if response1 is not None:
        scenario_ctx = {
            "delivery_id": (
                response1.delivery.delivery_id
                if response1.delivery
                else public1.get("delivery", {}).get("delivery_id")
            ),
            "quote_id": (response1.quote or {}).get("quote_id")
            if isinstance(response1.quote, dict)
            else None,
            "outcome": response1.outcome,
        }
        if response1.quote and isinstance(response1.quote, dict):
            scenario_ctx["quote_id"] = response1.quote.get("quote_id")

    for capture_key, capture_path in spec.capture.items():
        if capture_path == "delivery_id":
            scenario_ctx[capture_key] = scenario_ctx.get("delivery_id")
        elif capture_path == "quote_id":
            scenario_ctx[capture_key] = scenario_ctx.get("quote_id")
        elif capture_path.startswith("provenance_timestamp:"):
            attr = capture_path.split(":", 1)[1]
            scenario_ctx[capture_key] = extract_provenance_timestamp(public1, attr)

    context[spec.id] = scenario_ctx

    if spec.step2 is False or spec.step2 is None:
        return ScenarioResult(
            id=spec.id,
            phase=spec.phase,
            passed=True,
            skipped=False,
            detail="ok",
            request=step1_payload,
            response=public1,
        )

    if spec.step2 is True:
        step2_payload = {"delivery_id": scenario_ctx.get("delivery_id")}
    else:
        step2_payload = _resolve_template(
            dict(spec.step2),
            anchors=anchors,
            context=context,
        )
        if "delivery_id" not in step2_payload and scenario_ctx.get("delivery_id"):
            step2_payload.setdefault("delivery_id", scenario_ctx["delivery_id"])

    try:
        query2 = _build_query(step2_payload)
    except ValidationError as exc:
        return _invalid_query_result(
            spec,
            detail=f"invalid step2 query: {exc}",
            request=step2_payload,
        )
    response2 = run_query(query2)
    public2 = _public_dict(response2)

    failures = check_assertions(
        response2,
        public=public2,
        assertions=_resolve_template(spec.assert_step2, anchors=anchors, context=context),
        context=context,
        network_root=context.get("_network_root"),
    )
    if failures:
        return ScenarioResult(
            id=spec.id,
            phase=spec.phase,
            passed=False,
            skipped=False,
            detail="; ".join(failures),
            request=step2_payload,
            response=public2,
        )

    scenario_ctx["delivery_id"] = (
        response2.delivery.delivery_id
        if response2.delivery
        else public2.get("delivery", {}).get("delivery_id")
    )
    if response2.quote and isinstance(response2.quote, dict):
        scenario_ctx["quote_id"] = response2.quote.get("quote_id")
    for capture_key, capture_path in spec.capture.items():
        if capture_path == "delivery_id":
            scenario_ctx[capture_key] = scenario_ctx.get("delivery_id")
        elif capture_path == "quote_id":
            scenario_ctx[capture_key] = scenario_ctx.get("quote_id")
        elif capture_path.startswith("provenance_timestamp:"):
            attr = capture_path.split(":", 1)[1]
            scenario_ctx[capture_key] = extract_provenance_timestamp(public2, attr)
    context[spec.id] = scenario_ctx

    return ScenarioResult(
        id=spec.id,
        phase=spec.phase,
        passed=True,
        skipped=False,
        detail="ok",
        request=step2_payload,
        response=public2,
    )


def run_catalog(
    entry: NetworkEntry,
    *,
    phases: set[str] | None = None,
    network_root: Path | None = None,
) -> tuple[list[ScenarioResult], dict[str, Any]]:
    root = network_root or entry.default_root
    apply_network_paths(NetworkPaths.from_root(root))
    reset_query_runtime()

    anchors = load_anchors(entry.anchors_path)
    scenarios = filter_scenarios(load_catalog(entry.catalog_path), phases=phases)

    context: dict[str, Any] = {"_network_root": root}
    results: list[ScenarioResult] = []
    for spec in scenarios:
        reset_core_graph()
        result = run_scenario(spec, anchors=anchors, context=context)
        results.append(result)

    meta = {
        "network": entry.name,
        "network_root": str(root),
        "phases": sorted(phases) if phases else entry.phases,
        "scenario_count": len(results),
        "passed": sum(1 for item in results if item.passed and not item.skipped),
        "failed": sum(1 for item in results if not item.passed and not item.skipped),
        "skipped": sum(1 for item in results if item.skipped),
    }
    return results, meta


def discover_anchor_drift(
    entry: NetworkEntry,
    *,
    network_root: Path | None = None,
) -> dict[str, Any]:
    """Compare live root state to anchor JSON (entity counts, key stats)."""
    root = network_root or entry.default_root
    apply_network_paths(NetworkPaths.from_root(root))
    reset_query_runtime()

    anchors = load_anchors(entry.anchors_path)
    report: dict[str, Any] = {
        "network": entry.name,
        "network_root": str(root),
        "anchors_file": str(entry.anchors_path) if entry.anchors_path else None,
        "checks": [],
    }

    if entry.name in {"crm", "crm-metering"}:
        expected = anchors.get("seed_count")
        actual = get_entity_registry().entity_count()
        report["checks"].append(
            {
                "check": "registry_entity_count",
                "expected": expected,
                "actual": actual,
                "drift": actual != expected,
            },
        )

    if entry.name == "empty-crm":
        actual = get_entity_registry().entity_count()
        report["checks"].append(
            {
                "check": "registry_entity_count",
                "expected": 0,
                "actual": actual,
                "drift": actual != 0,
            },
        )

    if entry.name == "baseball" and anchors:
        player = str(anchors.get("player", "Hank Aaron"))
        attrs = {
            "career_hr": anchors.get("career_hr"),
            "career_avg": anchors.get("career_avg"),
            "career_rbi": anchors.get("career_rbi"),
            "career_hits": anchors.get("career_hits"),
            "career_wins": anchors.get("career_wins"),
            "career_strikeouts": anchors.get("career_strikeouts"),
            "height": anchors.get("height"),
            "weight": anchors.get("weight"),
            "birth_country": anchors.get("birth_country"),
            "final_game": anchors.get("final_game"),
            "death_date": anchors.get("death_date"),
            "hall_of_fame_year": anchors.get("hall_of_fame_year"),
            "fielding_percentage": anchors.get("fielding_percentage"),
        }
        pitcher = anchors.get("pitcher_player")
        if pitcher:
            for attr, key in (
                ("pitcher_career_wins", "career_wins"),
                ("pitcher_career_strikeouts", "career_strikeouts"),
                ("pitcher_career_era", "career_era"),
                ("pitcher_career_whip", "career_whip"),
                ("pitcher_k_per_9", "k_per_9"),
                ("pitcher_career_innings_pitched", "career_innings_pitched"),
            ):
                expected = anchors.get(attr)
                if expected is None:
                    continue
                q1 = EntityQuery(
                    lookup={"player": str(pitcher)},
                    requested_attributes=[key],
                )
                r1 = run_query(q1)
                if r1.outcome != "lookup_resolved" or not r1.delivery:
                    report["checks"].append(
                        {
                            "check": f"resolve_{key}_{pitcher}",
                            "expected": expected,
                            "actual": None,
                            "drift": True,
                            "detail": f"step1 outcome={r1.outcome!r}",
                        },
                    )
                    continue
                reset_core_graph()
                r2 = run_query(EntityQuery(delivery_id=r1.delivery.delivery_id))
                actual = r2.results[0].get(key) if r2.results else None
                drift = (
                    rate_value_drift(expected, actual)
                    if key in RATE_DRIFT_ATTRS
                    else str(actual) != str(expected)
                )
                report["checks"].append(
                    {
                        "check": f"resolve_{key}_{pitcher}",
                        "expected": expected,
                        "actual": actual,
                        "drift": drift,
                    },
                )
        team_label = anchors.get("team_label")
        if team_label:
            for attr in ("season_wins", "season_losses"):
                expected = anchors.get(attr)
                if expected is None:
                    continue
                q1 = EntityQuery(
                    lookup={"team": str(team_label)},
                    requested_attributes=[attr],
                )
                r1 = run_query(q1)
                if r1.outcome != "lookup_resolved" or not r1.delivery:
                    report["checks"].append(
                        {
                            "check": f"resolve_{attr}_{team_label}",
                            "expected": expected,
                            "actual": None,
                            "drift": True,
                            "detail": f"step1 outcome={r1.outcome!r}",
                        },
                    )
                    continue
                reset_core_graph()
                r2 = run_query(EntityQuery(delivery_id=r1.delivery.delivery_id))
                actual = r2.results[0].get(attr) if r2.results else None
                report["checks"].append(
                    {
                        "check": f"resolve_{attr}_{team_label}",
                        "expected": expected,
                        "actual": actual,
                        "drift": str(actual) != str(expected),
                    },
                )
            scoped_year = "1957"
            for attr, expected in (
                ("roster", anchors.get("roster_member_1957_bro")),
            ):
                if expected is None:
                    continue
                q1 = EntityQuery(
                    lookup={"team": str(team_label)},
                    scope={"yearID": scoped_year},
                    requested_attributes=[attr],
                )
                r1 = run_query(q1)
                if r1.outcome != "lookup_resolved" or not r1.delivery:
                    report["checks"].append(
                        {
                            "check": f"resolve_{attr}_{team_label}_{scoped_year}",
                            "expected": expected,
                            "actual": None,
                            "drift": True,
                            "detail": f"step1 outcome={r1.outcome!r}",
                        },
                    )
                    continue
                reset_core_graph()
                r2 = run_query(EntityQuery(delivery_id=r1.delivery.delivery_id))
                actual = r2.results[0].get(attr) if r2.results else None
                report["checks"].append(
                    {
                        "check": f"resolve_{attr}_{team_label}_{scoped_year}",
                        "expected": f"contains {expected!r}",
                        "actual": actual,
                        "drift": str(expected) not in str(actual),
                    },
                )
            franchise_expected = anchors.get("franchise_team_labels_json")
            if franchise_expected is not None:
                q1 = EntityQuery(
                    lookup={"team": str(team_label)},
                    requested_attributes=["franchise_teams"],
                )
                r1 = run_query(q1)
                if r1.outcome != "lookup_resolved" or not r1.delivery:
                    report["checks"].append(
                        {
                            "check": "resolve_franchise_teams",
                            "expected": franchise_expected,
                            "actual": None,
                            "drift": True,
                            "detail": f"step1 outcome={r1.outcome!r}",
                        },
                    )
                else:
                    reset_core_graph()
                    r2 = run_query(EntityQuery(delivery_id=r1.delivery.delivery_id))
                    actual = r2.results[0].get("franchise_teams") if r2.results else None
                    report["checks"].append(
                        {
                            "check": "resolve_franchise_teams",
                            "expected": franchise_expected,
                            "actual": actual,
                            "drift": str(actual) != str(franchise_expected),
                        },
                    )
        fielder = anchors.get("fielder_player")
        if fielder:
            for attr, key in (
                ("fielder_career_games", "career_games"),
                ("fielder_career_putouts", "career_putouts"),
            ):
                expected = anchors.get(attr)
                if expected is None:
                    continue
                q1 = EntityQuery(
                    lookup={"player": str(fielder)},
                    requested_attributes=[key],
                )
                r1 = run_query(q1)
                if r1.outcome != "lookup_resolved" or not r1.delivery:
                    report["checks"].append(
                        {
                            "check": f"resolve_{key}_{fielder}",
                            "expected": expected,
                            "actual": None,
                            "drift": True,
                            "detail": f"step1 outcome={r1.outcome!r}",
                        },
                    )
                    continue
                reset_core_graph()
                r2 = run_query(EntityQuery(delivery_id=r1.delivery.delivery_id))
                actual = r2.results[0].get(key) if r2.results else None
                report["checks"].append(
                    {
                        "check": f"resolve_{key}_{fielder}",
                        "expected": expected,
                        "actual": actual,
                        "drift": str(actual) != str(expected),
                    },
                )
        for attr, expected in attrs.items():
            if expected is None:
                continue
            q1 = EntityQuery(
                lookup={"player": player},
                requested_attributes=[attr],
            )
            r1 = run_query(q1)
            if r1.outcome != "lookup_resolved" or not r1.delivery:
                report["checks"].append(
                    {
                        "check": f"resolve_{attr}",
                        "expected": expected,
                        "actual": None,
                        "drift": True,
                        "detail": f"step1 outcome={r1.outcome!r}",
                    },
                )
                continue
            reset_core_graph()
            q2 = EntityQuery(delivery_id=r1.delivery.delivery_id)
            r2 = run_query(q2)
            actual = r2.results[0].get(attr) if r2.results else None
            drift = (
                rate_value_drift(expected, actual)
                if attr in RATE_DRIFT_ATTRS
                else str(actual) != str(expected)
            )
            report["checks"].append(
                {
                    "check": attr,
                    "expected": expected,
                    "actual": actual,
                    "drift": drift,
                },
            )

    report["drift_detected"] = any(item.get("drift") for item in report["checks"])
    return report


def fresh_derive_cache(root: Path) -> list[str]:
    """Remove baseball derive cache files before derive phase."""
    removed: list[str] = []
    for rel in _DERIVE_CACHE_REL_PATHS:
        path = root / rel
        if path.is_file():
            path.unlink()
            removed.append(rel)
    return removed


_DERIVE_CACHE_REL_PATHS = ("agents/batting/storage.json", "intent_map.json")


def derive_phase_in_scope(phases: set[str] | None) -> bool:
    return phases is None or "derive" in phases


def derive_cache_files_exist(root: Path) -> bool:
    return any((root / rel).is_file() for rel in _DERIVE_CACHE_REL_PATHS)


def should_fresh_derive(
    *,
    network: str,
    entry: NetworkEntry,
    phases: set[str] | None,
    fresh_derive_flag: bool,
    no_fresh_derive: bool,
) -> bool:
    if network != "baseball":
        return False
    if no_fresh_derive:
        return False
    if not derive_phase_in_scope(phases):
        return False
    return entry.fresh_derive_before_gate or fresh_derive_flag


def format_summary_table(results: list[ScenarioResult]) -> str:
    lines = ["scenario                          phase        status  detail"]
    for item in results:
        status = "SKIP" if item.skipped else ("PASS" if item.passed else "FAIL")
        lines.append(
            f"{item.id:32} {item.phase:12} {status:6}  {item.detail[:60]}",
        )
    return "\n".join(lines)
