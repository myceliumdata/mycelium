"""Long-lived localhost admin HTTP server (one process per network)."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

# Force the sync checkpointer path for the long-lived admin HTTP server.
# Matches MCP/CLI: avoids event-loop lock errors when run_query() is called
# from FastAPI worker threads with repeated asyncio.run() on the async saver.
os.environ["MYCELIUM_USE_SYNC_CHECKPOINTER"] = "1"

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agents.runtime import refresh_runtime_from_disk
from agents.entity_registry import reset_entity_registry
from graphs.core import run_query
from models.state import BillingPrincipal, EntityQuery, QueryResponse
from network.introspection import (
    build_network_capabilities,
    build_network_status,
    status_to_dict,
)
from network.paths import NO_NETWORK_CONFIGURED_MSG, NetworkPaths, apply_network_paths, resolve_network_root
from storage.core import get_storage

_NETWORK_INFO: dict[str, str | None] | None = None


class AdminQueryRequest(BaseModel):
    """Target-protocol query body (step 1: id/lookup; step 2: delivery_id)."""

    id: str | None = None
    lookup: dict[str, str] = Field(default_factory=dict)
    delivery_id: str | None = None
    requested_attributes: list[str] = Field(default_factory=list)
    thread_id: str | None = None
    quote_id: str | None = None
    provenance: bool = False
    principal: BillingPrincipal | None = None
    confirm_new_entity: bool = False


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
    """Drop cached entity registry so GET /status reflects on-disk entities.json."""
    reset_entity_registry()


def bootstrap_admin() -> dict[str, str | None]:
    """Bind network at process start; fail fast when unconfigured."""
    global _NETWORK_INFO
    load_dotenv()
    from network.paths import network_metadata

    root = resolve_network_root()
    paths = NetworkPaths.from_root(root)
    apply_network_paths(paths)
    get_storage(db_path=paths.db_path)
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
        allow_methods=["GET", "POST"],
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
        lookup: str | None = None,
    ) -> dict[str, Any]:
        """Read-only network snapshot. ``lookup`` is a JSON-encoded MVR bind map."""
        _refresh_read_cache()
        target_lookup: dict[str, str] | None = None
        if lookup:
            try:
                parsed = json.loads(lookup)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                target_lookup = {
                    str(key): str(value)
                    for key, value in parsed.items()
                    if str(value).strip()
                } or None
        summary = build_network_status(
            category_filter=category,
            entity_key=entity if not target_lookup else None,
            target_lookup=target_lookup,
        )
        return status_to_dict(summary)

    @app.get("/capabilities")
    def capabilities() -> dict[str, Any]:
        _refresh_read_cache()
        return build_network_capabilities()

    @app.post("/query")
    def query_entity(body: AdminQueryRequest) -> dict[str, Any]:
        refresh_runtime_from_disk()
        _refresh_read_cache()
        query = EntityQuery(
            id=body.id,
            lookup=dict(body.lookup),
            delivery_id=body.delivery_id,
            requested_attributes=body.requested_attributes,
            quote_id=body.quote_id,
            provenance=body.provenance,
            principal=body.principal,
            confirm_new_entity=body.confirm_new_entity,
        )
        thread_id = body.thread_id or f"admin-{uuid.uuid4()}"
        response: QueryResponse = run_query(query, thread_id=thread_id)
        return response.public_dict()

    _mount_admin_ui(app)
    return app


def _mount_admin_ui(app: FastAPI) -> None:
    """Serve built SPA from ``admin-ui/dist`` when present (demo single-process mode)."""
    from fastapi.staticfiles import StaticFiles
    from network.paths import framework_root

    dist = framework_root() / "admin-ui" / "dist"
    index = dist / "index.html"
    if index.is_file():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="admin-ui")
    else:
        print("admin UI: cd admin-ui && npm run build")


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
