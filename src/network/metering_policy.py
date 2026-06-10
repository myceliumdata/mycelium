"""Metering policy from ``network.json`` (Slice 10)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from network.paths import NetworkPaths, resolve_network_root

_DEFAULT_FUNDING_MODEL = "marginal"
_DEFAULT_QUOTE_PROVIDER = "builtin"
_DEFAULT_PRINCIPAL_REQUIRED_FOR = ("sponsor_public", "pool")
_DEFAULT_PAYMENT_PROVIDER = "mock"


@dataclass(frozen=True)
class PaymentPolicy:
    """Per-network payment settlement policy (Slice 11)."""

    enabled: bool
    provider: str
    require_paid_before_accept: bool

    def summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "require_paid_before_accept": self.require_paid_before_accept,
        }


@dataclass(frozen=True)
class MeteringPolicy:
    """Per-network workload pricing policy."""

    enabled: bool
    default_funding_model: str
    meter_first_delivery: bool
    quote_provider: str
    marginal_principal_optional: bool
    principal_required_for: tuple[str, ...]
    payment: PaymentPolicy

    def summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "default_funding_model": self.default_funding_model,
            "meter_first_delivery": self.meter_first_delivery,
            "quote_provider": self.quote_provider,
            "principal": {
                "marginal_optional": self.marginal_principal_optional,
                "required_for_funding_models": list(self.principal_required_for),
            },
            "payment": self.payment.summary(),
        }


def _crm_default_payment() -> PaymentPolicy:
    return PaymentPolicy(
        enabled=False,
        provider=_DEFAULT_PAYMENT_PROVIDER,
        require_paid_before_accept=True,
    )


def _parse_payment_block(raw: Any) -> PaymentPolicy | None:
    if not isinstance(raw, dict):
        return None
    enabled = bool(raw.get("enabled", False))
    provider = raw.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        provider = _DEFAULT_PAYMENT_PROVIDER
    require_paid = raw.get("require_paid_before_accept")
    if require_paid is None:
        require_paid_before_accept = True
    else:
        require_paid_before_accept = bool(require_paid)
    return PaymentPolicy(
        enabled=enabled,
        provider=provider.strip(),
        require_paid_before_accept=require_paid_before_accept,
    )


def _crm_default_metering() -> MeteringPolicy:
    return MeteringPolicy(
        enabled=False,
        default_funding_model=_DEFAULT_FUNDING_MODEL,
        meter_first_delivery=True,
        quote_provider=_DEFAULT_QUOTE_PROVIDER,
        marginal_principal_optional=True,
        principal_required_for=_DEFAULT_PRINCIPAL_REQUIRED_FOR,
        payment=_crm_default_payment(),
    )


def _parse_metering_block(raw: Any) -> MeteringPolicy | None:
    if not isinstance(raw, dict):
        return None
    enabled = bool(raw.get("enabled", False))
    funding = raw.get("default_funding_model")
    if not isinstance(funding, str) or not funding.strip():
        funding = _DEFAULT_FUNDING_MODEL
    meter_first = raw.get("meter_first_delivery")
    if meter_first is None:
        meter_first_delivery = True
    else:
        meter_first_delivery = bool(meter_first)
    provider = raw.get("quote_provider")
    if not isinstance(provider, str) or not provider.strip():
        provider = _DEFAULT_QUOTE_PROVIDER
    principal_block = raw.get("principal")
    marginal_optional = True
    required_for: list[str] = list(_DEFAULT_PRINCIPAL_REQUIRED_FOR)
    if isinstance(principal_block, dict):
        if "marginal_optional" in principal_block:
            marginal_optional = bool(principal_block.get("marginal_optional"))
        models = principal_block.get("required_for_funding_models")
        if isinstance(models, list) and models:
            required_for = [str(item).strip() for item in models if str(item).strip()]
    payment_block = raw.get("payment")
    payment = _parse_payment_block(payment_block) or _crm_default_payment()
    return MeteringPolicy(
        enabled=enabled,
        default_funding_model=funding.strip(),
        meter_first_delivery=meter_first_delivery,
        quote_provider=provider.strip(),
        marginal_principal_optional=marginal_optional,
        principal_required_for=tuple(required_for),
        payment=payment,
    )


def load_metering_policy(*, paths: NetworkPaths | None = None) -> MeteringPolicy:
    """Load metering policy from ``network.json``; disabled CRM default when absent."""
    if paths is None:
        root = resolve_network_root()
        paths = NetworkPaths.from_root(root)

    network_json = paths.root / "network.json"
    if not network_json.is_file():
        return _crm_default_metering()

    try:
        data = json.loads(network_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _crm_default_metering()

    if not isinstance(data, dict):
        return _crm_default_metering()

    parsed = _parse_metering_block(data.get("metering"))
    return parsed if parsed is not None else _crm_default_metering()
