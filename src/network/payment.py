"""Payment settlement providers behind metering quotes (Slice 11).

Future real x402 wiring may use ``MYCELIUM_X402_FACILITATOR_URL`` for facilitator
HTTP; the x402 stub provider ignores it today (CI-safe ``x402:test:`` proofs only).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Protocol

from pydantic import BaseModel

from models.state import BillingPrincipal
from network.credits import InsufficientCreditsError, get_credit_store
from network.metering_policy import PaymentPolicy, load_metering_policy
from network.quotes import Quote, QuoteStore, get_quote_store, quote_is_expired


class PaymentError(Exception):
    """Settlement failed (quote missing, expired, invalid proof, etc.)."""


class PaidReceipt(BaseModel):
    quote_id: str
    provider: str
    amount_usd: float
    proof: str | None = None
    settled_at: str


class PaymentProvider(Protocol):
    def settle(
        self,
        quote: Quote,
        *,
        proof: str | None = None,
        principal: BillingPrincipal | None = None,
    ) -> PaidReceipt: ...


class MockPaymentProvider:
    """Always succeeds; optional proof prefix ``test:`` for harnesses."""

    provider_name = "mock"

    def settle(
        self,
        quote: Quote,
        *,
        proof: str | None = None,
        principal: BillingPrincipal | None = None,
    ) -> PaidReceipt:
        _ = principal
        return PaidReceipt(
            quote_id=quote.quote_id,
            provider=self.provider_name,
            amount_usd=quote.total_usd,
            proof=proof,
            settled_at=datetime.now(timezone.utc).isoformat(),
        )


class CreditPaymentProvider:
    """Validate tenant balance; deduct happens in ``settle_quote`` after ``mark_paid``."""

    provider_name = "credit"

    def settle(
        self,
        quote: Quote,
        *,
        proof: str | None = None,
        principal: BillingPrincipal | None = None,
    ) -> PaidReceipt:
        _ = proof
        if principal is None or not principal.id.strip():
            msg = "credit settlement requires principal with tenant id"
            raise PaymentError(msg)
        tenant_id = principal.id.strip()
        store = get_credit_store()
        if not store.has_sufficient_balance(tenant_id, quote.total_usd):
            balance = store.get_balance(tenant_id)
            msg = (
                f"insufficient credits for tenant {tenant_id!r}: "
                f"need {quote.total_usd:.4f} have {balance:.4f}"
            )
            raise PaymentError(msg)
        return PaidReceipt(
            quote_id=quote.quote_id,
            provider=self.provider_name,
            amount_usd=quote.total_usd,
            proof=None,
            settled_at=datetime.now(timezone.utc).isoformat(),
        )


class X402StubPaymentProvider:
    """Accepts proof prefix ``x402:test:`` only (no facilitator HTTP in CI)."""

    provider_name = "x402_stub"

    def settle(
        self,
        quote: Quote,
        *,
        proof: str | None = None,
        principal: BillingPrincipal | None = None,
    ) -> PaidReceipt:
        _ = principal
        if not proof or not proof.startswith("x402:test:"):
            msg = "x402 stub requires proof prefix x402:test:"
            raise PaymentError(msg)
        return PaidReceipt(
            quote_id=quote.quote_id,
            provider=self.provider_name,
            amount_usd=quote.total_usd,
            proof=proof,
            settled_at=datetime.now(timezone.utc).isoformat(),
        )


_PROVIDERS: dict[str, type[MockPaymentProvider | CreditPaymentProvider | X402StubPaymentProvider]] = {
    "mock": MockPaymentProvider,
    "credit": CreditPaymentProvider,
    "x402_stub": X402StubPaymentProvider,
    "x402": X402StubPaymentProvider,
}


def get_payment_provider(*, provider_name: str | None = None) -> PaymentProvider:
    name = (provider_name or load_metering_policy().payment.provider).strip().lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        msg = f"unknown payment provider: {name!r}"
        raise PaymentError(msg)
    return cls()


def auto_settle_quotes_enabled() -> bool:
    if os.getenv("MYCELIUM_AUTO_SETTLE_QUOTES", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True
    from agents.metering_gate import auto_accept_quotes_enabled

    return auto_accept_quotes_enabled()


def payment_bypassed(policy: PaymentPolicy | None = None) -> bool:
    payment = policy or load_metering_policy().payment
    return not payment.enabled or auto_settle_quotes_enabled()


def _deduct_credit_after_paid(
    *,
    quote_id: str,
    quote: Quote,
    principal: BillingPrincipal | None,
    store: QuoteStore,
) -> None:
    if principal is None or not principal.id.strip():
        store.revert_paid(quote_id)
        msg = "credit settlement requires principal with tenant id"
        raise PaymentError(msg)
    try:
        get_credit_store().deduct(principal.id.strip(), quote.total_usd)
    except InsufficientCreditsError as exc:
        store.revert_paid(quote_id)
        raise PaymentError(str(exc)) from exc


def settle_quote(
    quote_id: str,
    *,
    proof: str | None = None,
    principal: BillingPrincipal | None = None,
    provider_name: str | None = None,
) -> PaidReceipt:
    """Mark a pending quote paid via the configured PaymentProvider."""
    store = get_quote_store()
    quote = store.get(quote_id)
    if quote is None:
        msg = f"quote not found: {quote_id!r}"
        raise PaymentError(msg)
    if quote.status == "paid":
        if quote_is_expired(quote):
            msg = f"quote {quote_id!r} expired"
            raise PaymentError(msg)
        return PaidReceipt(
            quote_id=quote.quote_id,
            provider=quote.payment_provider or "unknown",
            amount_usd=quote.total_usd,
            proof=quote.payment_proof,
            settled_at=quote.paid_at or datetime.now(timezone.utc).isoformat(),
        )
    if quote.status != "pending":
        msg = f"quote {quote_id!r} cannot be settled (status={quote.status!r})"
        raise PaymentError(msg)
    if quote_is_expired(quote):
        msg = f"quote {quote_id!r} expired"
        raise PaymentError(msg)

    provider = get_payment_provider(provider_name=provider_name)
    receipt = provider.settle(quote, proof=proof, principal=principal)
    marked = store.mark_paid(
        quote_id,
        provider=receipt.provider,
        proof=receipt.proof,
        settled_at=receipt.settled_at,
    )
    if marked is None:
        msg = f"failed to mark quote paid: {quote_id!r}"
        raise PaymentError(msg)
    if receipt.provider == CreditPaymentProvider.provider_name:
        _deduct_credit_after_paid(
            quote_id=quote_id,
            quote=quote,
            principal=principal,
            store=store,
        )
    return receipt
