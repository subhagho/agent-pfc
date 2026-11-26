"""Import direction between the project's packages.

Imports are read statically, so dynamic importing is forbidden outright.
"""

import ast
from pathlib import Path

ROOT = "agent_pfc"
SOURCE = Path(__file__).parents[1] / "src" / ROOT

# Package (or top-level module) -> what it may import from the project.
# A dotted entry allows that submodule only.
ALLOWED: dict[str, frozenset[str]] = {
    "domain": frozenset(),
    "probes": frozenset({"domain"}),
    "embeddings": frozenset(),
    "composition": frozenset({"domain"}),
    "evaluation": frozenset({"domain"}),
    "experiments": frozenset(
        {"domain", "composition", "evaluation", "embeddings.protocol"}
    ),
    "reporting": frozenset({"domain", "evaluation", "experiments"}),
    "cli": frozenset({"domain", "probes", "embeddings", "experiments", "reporting"}),
}


# Standard-library routes to importing a module by name, or to running code.
LOADER_MODULES = frozenset({"builtins", "importlib", "pkgutil", "runpy"})
DYNAMIC_BUILTINS = frozenset({"__builtins__", "__import__", "eval", "exec"})


def _imported_names(module: str, is_package: bool, source: str) -> list[str]:
    """Absolute dotted names of everything `source` imports from the project."""
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = module.split(".")
                parts = parts[: len(parts) - node.level + (1 if is_package else 0)]
                base = ".".join(parts + ([base] if base else []))
            # From the root or a package, the imported name may be a submodule.
            if base == ROOT or base.removeprefix(f"{ROOT}.") in ALLOWED:
                names += [f"{base}.{alias.name}" for alias in node.names]
            else:
                names.append(base)
    return [n for n in names if n == ROOT or n.startswith(f"{ROOT}.")]


def _dynamic_imports(source: str) -> list[str]:
    """Ways `source` could import a module that static reading would miss."""
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [a.name for a in node.names if _is_loader(a.name)]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            if _is_loader(node.module or ""):
                found.append(node.module or "")
        elif isinstance(node, ast.Name) and node.id in DYNAMIC_BUILTINS:
            found.append(node.id)
        elif isinstance(node, ast.Attribute) and node.attr == "__import__":
            found.append(node.attr)
    return found


def _is_loader(module: str) -> bool:
    return module.split(".")[0] in LOADER_MODULES


def violations(module: str, source: str, is_package: bool = False) -> list[str]:
    dynamic = [f"{module} uses {name}" for name in _dynamic_imports(source)]
    return dynamic + _static_violations(module, source, is_package)


def _static_violations(module: str, source: str, is_package: bool) -> list[str]:
    parts = module.split(".")
    if len(parts) == 1:  # the root package imports nothing from the project
        return [f"{module} imports {n}" for n in _imported_names(module, True, source)]
    owner = parts[1]
    if owner not in ALLOWED:
        return [f"{module}: package {owner!r} is not in the allowed table"]

    found = []
    for name in _imported_names(module, is_package, source):
        target = name.removeprefix(ROOT).removeprefix(".")
        if target == owner or target.startswith(f"{owner}."):
            continue
        if not any(
            target == allowed or target.startswith(f"{allowed}.")
            for allowed in ALLOWED[owner]
        ):
            found.append(f"{module} imports {name}")
    return found


def test_import_direction_follows_allowed_table() -> None:
    files = sorted(SOURCE.rglob("*.py"))
    assert files
    found = []
    for path in files:
        parts = list(path.relative_to(SOURCE.parent).with_suffix("").parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts.pop()
        found += violations(".".join(parts), path.read_text(), is_package)
    assert found == []


def test_import_direction_rejects_forbidden_examples() -> None:
    forbidden = [
        ("agent_pfc.domain.probe", "from agent_pfc.probes import loading"),
        ("agent_pfc.domain.probe", "from ..probes import loading"),
        ("agent_pfc.embeddings.cache", "import agent_pfc.domain"),
        ("agent_pfc.evaluation.ranking", "from agent_pfc import embeddings"),
        ("agent_pfc.experiments.collapse", "from agent_pfc.embeddings.ollama import X"),
        ("agent_pfc.experiments.collapse", "from agent_pfc.embeddings import X"),
        ("agent_pfc.reporting.markdown", "def f():\n    from agent_pfc import probes"),
        ("agent_pfc.cli", "import agent_pfc"),
        ("agent_pfc.domain.probe", "import importlib\nimportlib.import_module('x')"),
        ("agent_pfc.domain.probe", "from importlib import import_module"),
        ("agent_pfc.domain.probe", "__import__('agent_pfc.probes')"),
        ("agent_pfc.domain.probe", "import builtins\nbuiltins.__import__('x')"),
        ("agent_pfc.domain.probe", "import importlib.util\nimportlib.import_module('x')"),
        ("agent_pfc.domain.probe", "from importlib.util import find_spec"),
        ("agent_pfc.domain.probe", "import runpy"),
        ("agent_pfc.domain.probe", "exec('from agent_pfc import probes')"),
        ("agent_pfc.domain.probe", "from builtins import __import__ as load\nload('x')"),
        ("agent_pfc.domain.probe", "__builtins__['__imp' 'ort__']('x')"),
        ("agent_pfc.helpers", ""),
    ]
    for module, source in forbidden:
        assert violations(module, source), (module, source)


def test_import_direction_accepts_allowed_examples() -> None:
    allowed = [
        ("agent_pfc.domain.probe", "from agent_pfc.domain.modality import Modality"),
        ("agent_pfc.domain.probe", "from .modality import Modality"),
        ("agent_pfc.probes.loading", "from agent_pfc.domain import ProbeSet"),
        ("agent_pfc.experiments.collapse", "from agent_pfc.embeddings.protocol import X"),
        ("agent_pfc.experiments.collapse", "from agent_pfc.embeddings import protocol"),
        ("agent_pfc.cli", "from agent_pfc.embeddings.ollama import X"),
    ]
    for module, source in allowed:
        assert violations(module, source) == [], (module, source)

    # A package's relative import stays inside that package.
    assert violations("agent_pfc.domain", "from .modality import Modality", True) == []
