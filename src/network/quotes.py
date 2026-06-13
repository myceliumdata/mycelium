"""Quote issuance and builtin pricing (Slice 10)."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from models.state import BillingPrincipal
from network.entitlements import get_entitlement_store
from network.metering_policy import MeteringPolicy
from network.paths import runtime_path

CacheState = Literal["hit", "miss", "partial"]


class WorkloadSpec(BaseModel):
    entity_id: str = ""
    delivery_id: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    requested_attributes: list[str] = Field(default_factory=list)
    provenance: bool = False
    create_on_deliver: bool = False
    scope_hash: str = ""


class LineItem(BaseModel):
    kind: str
    meter: str
    amount_usd: float
    description: str


class Quote(BaseModel):
    quote_id: str
    expires_at: str
    workload: WorkloadSpec
    cache_state: CacheState
    funding_model: str
    line_items: list[LineItem] = Field(default_factory=list)
    total_usd: float = 0.0
    avoidable_cost: dict[str, Any] | None = None
    entitlement_offer: dict[str, Any] | None = None
    status: str = "pending"
    payment_provider: str | None = None
    payment_proof: str | None = None
    paid_at: str | None = None


class QuotesDocument(BaseModel):
    version: str = "1.0"
    quotes: dict[str, Quote] = Field(default_factory=dict)


_quote_store: "QuoteStore | None" = None


def reset_quote_store() -> None:
    global _quote_store
    _quote_store = None


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def meter_research_usd() -> float:
    return _env_float("MYCELIUM_METER_RESEARCH_USD", 2.0)


def meter_query_value_usd() -> float:
    return _env_float("MYCELIUM_METER_QUERY_VALUE_USD", 0.05)


def meter_query_provenance_usd() -> float:
    return _env_float("MYCELIUM_METER_QUERY_PROVENANCE_USD", 0.15)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def quote_ttl_seconds() -> int:
    return _env_int("MYCELIUM_QUOTE_TTL_SEC", 300)


def quote_is_expired(quote: Quote, *, now: datetime | None = None) -> bool:
    """Return True when ``quote.expires_at`` is in the past (or unparseable)."""
    try:
        expires = datetime.fromisoformat(quote.expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current >= expires


def compute_scope_hash(workload: WorkloadSpec) -> str:
    if (workload.delivery_id or "").strip():
        payload = {
            "delivery_id": workload.delivery_id,
            "entity_ids": sorted(workload.entity_ids),
            "requested_attributes": sorted(workload.requested_attributes),
            "provenance": workload.provenance,
            "create_on_deliver": workload.create_on_deliver,
        }
    else:
        payload = {
            "entity_id": workload.entity_id,
            "requested_attributes": sorted(workload.requested_attributes),
            "provenance": workload.provenance,
        }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    return f"sha256:{digest}"


def principal_required_error(
    funding_model: str,
    policy: MeteringPolicy,
    principal: BillingPrincipal | None,
) -> str | None:
    if funding_model not in policy.principal_required_for:
        return None
    if principal is not None and principal.id.strip():
        return None
    return f"principal required for funding_model={funding_model!r}"


class QuoteProvider(Protocol):
    def quote(
        self,
        *,
        workload: WorkloadSpec,
        cache_state: CacheState,
        funding_model: str,
        policy: MeteringPolicy,
        principal: BillingPrincipal | None,
    ) -> Quote: ...


class BuiltinQuoteProvider:
    """Fixed USD table; marginal cache-hit swaps production for consumption."""

    def quote(
        self,
        *,
        workload: WorkloadSpec,
        cache_state: CacheState,
        funding_model: str,
        policy: MeteringPolicy,
        principal: BillingPrincipal | None,
    ) -> Quote:
        _ = principal
        if workload.create_on_deliver and not workload.entity_ids:
            entity_count = 1
        elif workload.entity_ids:
            entity_count = len(workload.entity_ids)
        else:
            entity_count = 1 if workload.entity_id else 1
        research_usd = meter_research_usd() * entity_count
        query_usd = (
            meter_query_provenance_usd()
            if workload.provenance
            else meter_query_value_usd()
        ) * entity_count
        batch_note = f" (×{entity_count} entities)" if entity_count > 1 else ""
        line_items: list[LineItem] = []
        avoidable: dict[str, Any] | None = None
        include_production = cache_state in {"miss", "partial"} or funding_model == "full_duplicate"
        if include_production and cache_state == "hit" and funding_model != "full_duplicate":
            include_production = False
        if funding_model == "full_duplicate":
            include_production = True

        if include_production:
            line_items.append(
                LineItem(
                    kind="production",
                    meter="research",
                    amount_usd=research_usd,
                    description=f"Tavily research commit{batch_note}",
                ),
            )

        include_consumption = policy.meter_first_delivery or cache_state == "hit"
        if not policy.meter_first_delivery and cache_state in {"miss", "partial"}:
            include_consumption = False
        if include_consumption:
            meter = "query_provenance" if workload.provenance else "query_value"
            line_items.append(
                LineItem(
                    kind="consumption",
                    meter=meter,
                    amount_usd=query_usd,
                    description=f"Cache read / query delivery{batch_note}",
                ),
            )

        if cache_state == "hit" and funding_model == "marginal" and include_production is False:
            avoidable = {
                "research_usd": research_usd,
                "if": "query_only_accepted",
            }
            ent = get_entitlement_store().lookup_by_scope_hash(workload.scope_hash)
            if ent is not None:
                avoidable["entitlement_id"] = ent.entitlement_id

        total = round(sum(item.amount_usd for item in line_items), 4)
        now = datetime.now(timezone.utc)
        entitlement_id = f"ent_{uuid.uuid4().hex[:12]}"
        return Quote(
            quote_id=f"q_{uuid.uuid4().hex[:12]}",
            expires_at=(now + timedelta(seconds=quote_ttl_seconds())).isoformat(),
            workload=workload,
            cache_state=cache_state,
            funding_model=funding_model,
            line_items=line_items,
            total_usd=total,
            avoidable_cost=avoidable,
            entitlement_offer={
                "entitlement_id": entitlement_id,
                "covers": ["production"],
                "sponsor_id": principal.id if principal else None,
            },
        )


class QuoteStore:
    """Atomic JSON store for issued quotes."""

    def __init__(self, path: str | None = None) -> None:
        self.path = (
            runtime_path("MYCELIUM_QUOTES_PATH")
            if path is None
            else __import__("pathlib").Path(path)
        )
        self._data = QuotesDocument()
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(raw, dict):
            self._data = QuotesDocument.model_validate(raw)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._data.model_dump_json(indent=2)
        fd, tmp_path = tempfile.mkstemp(dir=self.path.parent, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(tmp_path, self.path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def issue(self, quote: Quote) -> Quote:
        self._data.quotes[quote.quote_id] = quote
        self._save()
        return quote

    def get(self, quote_id: str) -> Quote | None:
        return self._data.quotes.get(quote_id)

    def mark_paid(
        self,
        quote_id: str,
        *,
        provider: str,
        proof: str | None,
        settled_at: str,
    ) -> Quote | None:
        quote = self.get(quote_id)
        if quote is None:
            return None
        if quote.status == "paid":
            return quote
        if quote.status != "pending":
            return None
        paid = quote.model_copy(
            update={
                "status": "paid",
                "payment_provider": provider,
                "payment_proof": proof,
                "paid_at": settled_at,
            },
        )
        self._data.quotes[quote_id] = paid
        self._save()
        return paid

    def revert_paid(self, quote_id: str) -> Quote | None:
        """Restore a paid quote to pending (credit deduct rollback)."""
        quote = self.get(quote_id)
        if quote is None or quote.status != "paid":
            return None
        reverted = quote.model_copy(
            update={
                "status": "pending",
                "payment_provider": None,
                "payment_proof": None,
                "paid_at": None,
            },
        )
        self._data.quotes[quote_id] = reverted
        self._save()
        return reverted

    def accept(self, quote_id: str, *, require_paid: bool = False) -> Quote | None:
        quote = self.get(quote_id)
        if quote is None:
            return None
        if quote.status == "accepted":
            return quote
        if quote_is_expired(quote):
            return None
        if require_paid and quote.status != "paid":
            return None
        accepted = quote.model_copy(update={"status": "accepted"})
        self._data.quotes[quote_id] = accepted
        self._save()
        return accepted

    def all_quotes(self) -> dict[str, Quote]:
        return dict(self._data.quotes)


def get_quote_store() -> QuoteStore:
    global _quote_store
    if _quote_store is None:
        _quote_store = QuoteStore()
    return _quote_store


def quote_payload(quote: Quote) -> dict[str, Any]:
    data = quote.model_dump()
    data.pop("status", None)
    return data
