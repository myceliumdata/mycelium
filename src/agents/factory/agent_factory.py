"""Agent Factory (Jinja2 templates + generation + git commit + dynamic registration).

See approved plan Step 4 for full design and create_specialist contract.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jinja2

from agents.registry import RegisteredAgent, get_agent_registry
from agents.specialists.base import registry_storage_paths
from agents.specialists.protocol import dispatch_ensure_category_storage

logger = logging.getLogger(__name__)

_AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*_specialist$")


def _default_specialists_dir() -> Path:
    from network.paths import runtime_path

    return runtime_path("MYCELIUM_SPECIALISTS_DIR")


class AgentFactory:
    """Renders specialist agents, registers them, and optionally commits artifacts."""

    def __init__(
        self,
        registry: Any | None = None,
        specialists_dir: Path | None = None,
    ) -> None:
        self.registry = registry or get_agent_registry()
        self.specialists_dir = specialists_dir or _default_specialists_dir()
        templates_dir = Path(__file__).parent / "templates"
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def create_specialist(
        self,
        category: str,
        agent_name: str,
        description: str,
        examples: list[str] | None = None,
        *,
        llm_refine: bool = False,
        auto_commit: bool = False,
    ) -> dict[str, Any]:
        if not _AGENT_NAME_RE.match(agent_name):
            raise ValueError(
                f"Invalid agent_name {agent_name!r}: must match "
                r"^[a-z][a-z0-9_]*_specialist$"
            )

        if self.registry.has_agent(agent_name):
            return {"created": False, "reason": "already registered"}

        py_path = self.render_specialist_py(
            category=category,
            agent_name=agent_name,
            description=description,
            examples=examples,
            llm_refine=llm_refine,
        )
        now = datetime.now(timezone.utc).isoformat()

        dispatch_ensure_category_storage(category)
        storage_path, strategy_path = registry_storage_paths(category)

        entry = RegisteredAgent(
            name=agent_name,
            category=category,
            description=description,
            module_path=f"agents.specialists.{agent_name}",
            entrypoint=agent_name,
            storage_path=storage_path,
            strategy_path=strategy_path,
            is_generated=True,
            created_at=now,
        )
        self.registry.register_agent(entry)
        fn = self.registry.get_agent_fn(agent_name)

        committed = False
        if (
            auto_commit
            and "pytest" not in sys.modules
            and os.getenv("MYCELIUM_FACTORY_AUTO_COMMIT", "0") == "1"
        ):
            committed = self._commit_artifacts(py_path, agent_name, category)

        return {
            "created": True,
            "agent_name": agent_name,
            "category": category,
            "path": str(py_path),
            "committed": committed,
            "fn_loaded": callable(fn),
            "registry_path": str(self.registry.registry_path),
        }

    def render_specialist_py(
        self,
        *,
        category: str,
        agent_name: str,
        description: str,
        examples: list[str] | None = None,
        llm_refine: bool = False,
        created_at: str | None = None,
    ) -> Path:
        """Render specialist_agent.py.j2 and write the module (no registry registration)."""
        if not _AGENT_NAME_RE.match(agent_name):
            raise ValueError(
                f"Invalid agent_name {agent_name!r}: must match "
                r"^[a-z][a-z0-9_]*_specialist$"
            )

        template = self.env.get_template("specialist_agent.py.j2")
        now = created_at or datetime.now(timezone.utc).isoformat()
        raw_code = template.render(
            agent_name=agent_name,
            category=category,
            description=description,
            examples=examples or [],
            created_at=now,
        )
        code = raw_code
        if llm_refine:
            code = self._refine_with_llm(raw_code, agent_name)

        self.specialists_dir.mkdir(parents=True, exist_ok=True)
        py_path = self.specialists_dir / f"{agent_name}.py"
        py_path.write_text(code, encoding="utf-8")
        return py_path

    def regenerate_specialists_from_registry(
        self,
        *,
        registry_path: Path | None = None,
        categories_path: Path | None = None,
    ) -> list[Path]:
        """Re-render all registered generated specialists from the Jinja template."""
        from network.paths import runtime_path

        reg_path = registry_path or runtime_path("MYCELIUM_AGENT_REGISTRY_PATH")
        cat_path = categories_path or runtime_path("MYCELIUM_CATEGORIES_PATH")
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        categories: dict[str, Any] = {}
        if cat_path.is_file():
            cat_doc = json.loads(cat_path.read_text(encoding="utf-8"))
            categories = cat_doc.get("categories", {})

        written: list[Path] = []
        for entry in reg.get("agents", {}).values():
            if not entry.get("is_generated"):
                continue
            agent_name = entry["name"]
            category = entry["category"]
            cat_meta = categories.get(category, {})
            description = entry.get("description") or cat_meta.get("description", "")
            examples = cat_meta.get("examples") or []
            written.append(
                self.render_specialist_py(
                    category=category,
                    agent_name=agent_name,
                    description=description,
                    examples=examples,
                ),
            )
        return written

    def _refine_with_llm(self, code: str, agent_name: str) -> str:
        """Optional LLM polish (off by default per lightweight).

        The Jinja2 template and approved plan design remain the source of truth.
        When used, output is still committed for human review (real runs only).
        """
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        prompt = (
            "You are an expert Python developer maintaining the Mycelium project. "
            "Review the following generated specialist agent code for consistency "
            "with project style (see agents/supervisor.py and specialist template: "
            "thin _coerce, SpecialistStorage keyed by id (UUID), context + "
            "target_fields, 3 scenarios, specialist_contrib, response builders). Keep all "
            "functionality and structure. Improve comments/docstrings if missing "
            "or unclear. Output ONLY the complete valid Python source code, "
            "no markdown fences or explanation.\n\n"
            f"{code}"
        )
        resp = llm.invoke(prompt)
        improved = (resp.content if hasattr(resp, "content") else str(resp)).strip()
        if agent_name in improved and f"def {agent_name}" in improved:
            return improved
        return code

    def _find_repo_root(self, start: Path) -> Path | None:
        current = start.resolve()
        for directory in (current, *current.parents):
            if (directory / ".git").is_dir():
                return directory
        return None

    def _commit_artifacts(
        self,
        py_path: Path,
        agent_name: str,
        category: str,
    ) -> bool:
        root = self._find_repo_root(py_path)
        if root is None:
            logger.debug("AgentFactory: no git root found; skipping commit")
            return False

        try:
            rel_py = py_path.resolve().relative_to(root)
            rel_registry = self.registry.registry_path.resolve().relative_to(root)
            data_dir = root / "data" / "agents" / category
            paths = [str(rel_py), str(rel_registry)]
            if (data_dir / "storage.json").exists():
                paths.append(str((data_dir / "storage.json").relative_to(root)))
            if (data_dir / "storage_strategy.json").exists():
                paths.append(
                    str((data_dir / "storage_strategy.json").relative_to(root)),
                )

            subprocess.run(
                ["git", "add", *paths],
                cwd=root,
                check=True,
                capture_output=True,
            )
            msg = (
                f"feat(agents): auto-generate {agent_name} for category '{category}'"
            )
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=root,
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, OSError, ValueError) as exc:
            logger.warning("AgentFactory: git commit failed: %s", exc)
            return False


_agent_factory: AgentFactory | None = None


def get_agent_factory() -> AgentFactory:
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory()
    return _agent_factory


def reset_agent_factory() -> None:
    global _agent_factory
    _agent_factory = None
