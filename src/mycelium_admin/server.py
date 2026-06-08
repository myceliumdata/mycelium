"""Long-lived localhost admin HTTP server (one process per network)."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agents.seed import reset_seed_data
from network.introspection import (
    build_network_capabilities,
    build_network_status,
    status_to_dict,
)
from network.paths import NO_NETWORK_CONFIGURED_MSG, NetworkPaths, apply_network_paths, resolve_network_root
from storage.core import get_storage

_NETWORK_INFO: dict[str, str | None] | None = None

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8741


def _admin_host() -> str:
    return os.getenv("MYCELIUM_ADMIN_HOST", _DEFAULT_HOST).strip() or _DEFAULT_HOST


def _admin_port() -> int:
    raw = os.getenv("MYCELIUM_ADMIN_PORT", str(_DEFAULT_PORT)).strip()
    try:
        return int(raw)
    except ValueError:
        return _DEFAULT_PORT


def _refresh_read_cache() -> None:
    """Drop cached seed so GET /status reflects on-disk seed.json after refresh."""
    reset_seed_data()


def bootstrap_admin() -> dict[str, str | None]:
    """Bind network at process start; fail fast when unconfigured."""
    global _NETWORK_INFO
    load_dotenv()
    from network.paths import network_metadata

    root = resolve_network_root()
    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)
    get_storage(db_path=paths.db_path, seed_path=paths.seed_path)
    _NETWORK_INFO = network_metadata(root=paths.root)
    return _NETWORK_INFO


def _health_payload() -> dict[str, Any]:
    if _NETWORK_INFO is None:
        return {
            "status": "error",
            "message": NO_NETWORK_CONFIGURED_MSG,
        }
    return {
        "status": "ok",
        "network_name": _NETWORK_INFO.get("network_name"),
        "display_name": _NETWORK_INFO.get("network_display_name"),
        "network_root": _NETWORK_INFO.get("network_root"),
    }


def create_app() -> FastAPI:
    """Build the FastAPI application (bootstrap separately via ``bootstrap_admin``)."""
    app = FastAPI(title="Mycelium Admin", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(127\.0\.0\.1|localhost)(:\d+)?",
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=None)
    def health() -> JSONResponse:
        payload = _health_payload()
        status_code = 503 if payload.get("status") == "error" else 200
        return JSONResponse(status_code=status_code, content=payload)

    @app.get("/status")
    def status(
        category: str | None = None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        _refresh_read_cache()
        summary = build_network_status(
            category_filter=category,
            entity_key=entity,
        )
        return status_to_dict(summary)

    @app.get("/capabilities")
    def capabilities() -> dict[str, Any]:
        _refresh_read_cache()
        return build_network_capabilities()

    return app


def run_server() -> None:
    """Entry point for ``mycelium-admin`` script."""
    import uvicorn

    info = bootstrap_admin()
    host = _admin_host()
    port = _admin_port()
    root = info.get("network_root") or "?"
    name = info.get("network_name") or info.get("network_display_name") or "network"
    print(f"Mycelium admin: {name} @ {root}")
    print(f"Listening on http://{host}:{port}")
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    run_server()
