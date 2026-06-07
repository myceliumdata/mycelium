"""Runtime refresh for long-lived processes (MCP server).

The CLI starts a new process per query; MCP stays alive and must reload disk-backed
singletons and dynamically imported specialist modules before each tool call.
"""

from __future__ import annotations

import os
import re
import sys

from dotenv import load_dotenv

from agents.classification import get_category_tree, reset_category_tree
from agents.factory.agent_factory import reset_agent_factory
from agents.registry import get_agent_registry, reset_agent_registry
from agents.seed import get_seed_data, reset_seed_data

_GENERATED_SPECIALIST_MODULE_RE = re.compile(
    r"^agents\.specialists\.[a-z][a-z0-9_]*_specialist$",
)

_NETWORK_PATH_ENV_KEYS = (
    "MYCELIUM_NETWORK_ROOT",
    "MYCELIUM_SEED_PATH",
    "MYCELIUM_AGENT_REGISTRY_PATH",
    "MYCELIUM_CATEGORIES_PATH",
    "MYCELIUM_AGENT_DATA_DIR",
    "MYCELIUM_SPECIALISTS_DIR",
    "MYCELIUM_CHECKPOINT_PATH",
    "MYCELIUM_DB_PATH",
)


def evict_cached_specialist_modules() -> list[str]:
    """Remove dynamically loaded specialist modules so the next invoke re-reads disk."""
    removed: list[str] = []
    for key in list(sys.modules):
        if key.startswith("dyn_specialist_"):
            removed.append(key)
            del sys.modules[key]
            continue
        if _GENERATED_SPECIALIST_MODULE_RE.match(key):
            removed.append(key)
            del sys.modules[key]
    return removed


def refresh_runtime_from_disk(*, reload_dotenv: bool = True) -> None:
    """
    Reload registry, categories, seed, and specialist modules from current env paths.

    Does not reset the LangGraph checkpointer (``reset_core_graph``) — MCP needs
    ``thread_id`` continuity across queries in one process.
    """
    preserved_paths = {
        key: os.environ[key] for key in _NETWORK_PATH_ENV_KEYS if key in os.environ
    }
    if reload_dotenv:
        load_dotenv(override=True)
    if preserved_paths:
        os.environ.update(preserved_paths)

    reset_agent_registry()
    get_agent_registry()

    reset_category_tree()
    get_category_tree()

    reset_seed_data()
    get_seed_data()

    reset_agent_factory()
    evict_cached_specialist_modules()
