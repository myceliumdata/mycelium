"""Credit ledger for tenant balances (Slice 11 payment settlement)."""

from __future__ import annotations

import json
import os
import tempfile
from pydantic import BaseModel, Field

from network.paths import runtime_path


class InsufficientCreditsError(Exception):
    """Raised when a tenant balance cannot cover a settlement amount."""


class CreditsDocument(BaseModel):
    version: str = "1.0"
    balances: dict[str, float] = Field(default_factory=dict)


_credit_store: "CreditStore | None" = None


def reset_credit_store() -> None:
    global _credit_store
    _credit_store = None


class CreditStore:
    """Atomic JSON ledger mapping tenant id → balance_usd."""

    def __init__(self, path: str | None = None) -> None:
        self.path = (
            runtime_path("MYCELIUM_CREDITS_PATH")
            if path is None
            else __import__("pathlib").Path(path)
        )
        self._data = CreditsDocument()
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(raw, dict):
            self._data = CreditsDocument.model_validate(raw)

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

    def get_balance(self, tenant_id: str) -> float:
        return float(self._data.balances.get(tenant_id, 0.0))

    def has_sufficient_balance(self, tenant_id: str, amount_usd: float) -> bool:
        return self.get_balance(tenant_id) >= amount_usd

    def set_balance(self, tenant_id: str, balance_usd: float) -> None:
        self._data.balances[tenant_id] = round(balance_usd, 4)
        self._save()

    def deduct(self, tenant_id: str, amount_usd: float) -> float:
        balance = self.get_balance(tenant_id)
        if amount_usd > balance:
            msg = (
                f"insufficient credits for tenant {tenant_id!r}: "
                f"need {amount_usd:.4f} have {balance:.4f}"
            )
            raise InsufficientCreditsError(msg)
        new_balance = round(balance - amount_usd, 4)
        self._data.balances[tenant_id] = new_balance
        self._save()
        return new_balance


def get_credit_store() -> CreditStore:
    global _credit_store
    if _credit_store is None:
        _credit_store = CreditStore()
    return _credit_store
