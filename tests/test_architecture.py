"""Import direction between the project's packages, and no cycle between modules.

Imports are read statically, so dynamic importing is forbidden outright.
"""

import ast
import sys
from collections.abc import Collection
from graphlib import CycleError, TopologicalSorter
from pathlib import Path

import pytest

ROOT = "agent_pfc"
SOURCE = Path(__file__).parents[1] / "src" / ROOT

# Dotted package path below the root -> what it may import from the project.
# An entry allows that package or module, and everything below it.
# A module belongs to the longest key that prefixes its path.
ALLOWED: dict[str, frozenset[str]] = {
    "core.common": frozenset({"core.utils"}),
    "core.utils": frozenset({"core.common"}),
    "core.locations": frozenset({"core.common", "core.utils"}),
    "core.identity": frozenset({"core.common", "core.utils"}),
    "core.cache.embedding": frozenset({"core.common", "core.utils"}),
    "core.config": frozenset({"core.common", "core.utils", "core.locations"}),
    "core.activity": frozenset(
        {"core.common", "core.utils", "core.locations", "core.config"}
    ),
    "core.client": frozenset(
        {"core.common", "core.utils", "core.config", "core.activity"}
    ),
    "embeddings": frozenset(),
}

# Packages that only group other packages: their __init__ holds only a docstring.
NAMESPACES: frozenset[str] = frozenset({"core", "core.cache"})

# Nothing under this package imports the project from outside it.
CORE = "core"

# Standard-library routes to importing a module by name, or to running code.
LOADER_MODULES = frozenset({"builtins", "importlib", "pkgutil", "runpy"})
DYNAMIC_BUILTINS = frozenset({"__builtins__", "__import__", "eval", "exec"})

# Dotted module name -> (source, whether it is a package's __init__).
Modules = dict[str, tuple[str, bool]]


def _within(path: str, package: str) -> bool:
    return path == package or path.startswith(f"{package}.")


def _imported_names(
    module: str, is_package: bool, source: str, packages: Collection[str]
) -> list[str]:
    """Absolute dotted names of everything `source` imports from the project.

    Importing from one of `packages` may name a submodule, so each imported
    name is kept; importing from anything else counts as importing that module.
    """
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
            if base in packages:
                names += [f"{base}.{alias.name}" for alias in node.names]
            else:
                names.append(base)
    return [n for n in names if _within(n, ROOT)]


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


def _only_docstring(source: str) -> bool:
    body = ast.parse(source).body
    return not body or (
        len(body) == 1
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    )


def violations(module: str, source: str, is_package: bool = False) -> list[str]:
    dynamic = [f"{module} uses {name}" for name in _dynamic_imports(source)]
    return dynamic + _static_violations(module, source, is_package)


def _static_violations(module: str, source: str, is_package: bool) -> list[str]:
    packages = {ROOT} | {f"{ROOT}.{p}" for p in (*ALLOWED, *NAMESPACES)}
    imported = _imported_names(module, is_package, source, packages)
    if module == ROOT:  # the root package imports nothing from the project
        return [f"{module} imports {n}" for n in imported]

    path = module.removeprefix(f"{ROOT}.")
    owner = max((key for key in ALLOWED if _within(path, key)), key=len, default=None)
    if owner is None:
        if not (is_package and path in NAMESPACES):
            return [f"{module} is not in the allowed table"]
        if not _only_docstring(source):
            return [f"{module} is a namespace and holds more than a docstring"]
        return []

    found = []
    for name in imported:
        target = name.removeprefix(ROOT).removeprefix(".")
        if _within(owner, CORE) and not _within(target, CORE):
            found.append(f"{module} imports {name}, which is outside the core")
        elif not any(_within(target, p) for p in (owner, *ALLOWED[owner])):
            found.append(f"{module} imports {name}")
    return found


def _also_run(target: str, module: str) -> list[str]:
    """`target`, and the packages above it that importing it from `module` runs.

    A package above `module` is already being imported, so passing through it
    adds nothing. Naming it as the target still counts.
    """
    parts = target.split(".")
    above = [".".join(parts[:end]) for end in range(1, len(parts))]
    return [target] + [name for name in above if not _within(module, name)]


def cycles(modules: Modules) -> list[str]:
    """One import cycle among `modules`, naming them, or nothing if none."""
    # Any parent of a module is a package, with or without an __init__.
    packages = {name for name, (_, is_package) in modules.items() if is_package}
    packages |= {n[:i] for n in modules for i, char in enumerate(n) if char == "."}
    graph: dict[str, set[str]] = {}
    for module, (source, is_package) in modules.items():
        graph[module] = set()
        for name in _imported_names(module, is_package, source, packages):
            # The imported name may be an attribute: find the module holding it.
            while name and name not in modules:
                name = name.rpartition(".")[0]
            if name:
                graph[module].update(
                    run
                    for run in _also_run(name, module)
                    if run in modules and run != module
                )
    try:
        TopologicalSorter(graph).prepare()
    except CycleError as error:
        # graphlib lists each module before the one that imports it.
        return [f"import cycle: {' -> '.join(reversed(error.args[1]))}"]
    return []


def _source_modules() -> Modules:
    modules: Modules = {}
    for path in sorted(SOURCE.rglob("*.py")):
        parts = list(path.relative_to(SOURCE.parent).with_suffix("").parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts.pop()
        modules[".".join(parts)] = (path.read_text(), is_package)
    return modules


def test_real_source_tree_follows_table_and_has_no_module_cycle() -> None:
    modules = _source_modules()
    assert modules
    found = []
    for module, (source, is_package) in modules.items():
        found += violations(module, source, is_package)
    assert found + cycles(modules) == []


@pytest.mark.parametrize(
    ("module", "source"),
    [
        # core.common imports only common and utils.
        ("agent_pfc.core.common.entries", "from agent_pfc.core.config import X"),
        ("agent_pfc.core.common.entries", "from ..client import send"),
        ("agent_pfc.core.common.entries", "from agent_pfc.core import config"),
        ("agent_pfc.core.common.entries", "from .. import config"),
        ("agent_pfc.core.common.entries", "def f():\n    from agent_pfc import core"),
        ("agent_pfc.core.common.entries", "import agent_pfc"),
        # Other table edges.
        ("agent_pfc.core.utils.validation", "from agent_pfc.core.locations import X"),
        ("agent_pfc.core.config.loader", "import agent_pfc.core.activity"),
        ("agent_pfc.embeddings.cache", "from agent_pfc.core.common import X"),
        # Nothing under core imports the project from outside it.
        ("agent_pfc.core.common.entries", "from agent_pfc.embeddings import cache"),
        # Unlisted packages and modules.
        ("agent_pfc.helpers", ""),
        ("agent_pfc.core.helpers", ""),
        ("agent_pfc.core.cache.query.store", ""),
        # The root imports nothing from the project.
        ("agent_pfc", "import agent_pfc.core.common"),
        # Dynamic importing.
        ("agent_pfc.core.common.x", "import importlib\nimportlib.import_module('x')"),
        ("agent_pfc.core.common.x", "from importlib import import_module"),
        ("agent_pfc.core.common.x", "__import__('agent_pfc.core')"),
        ("agent_pfc.core.common.x", "import builtins\nbuiltins.__import__('x')"),
        ("agent_pfc.core.common.x", "import importlib.util"),
        ("agent_pfc.core.common.x", "from importlib.util import find_spec"),
        ("agent_pfc.core.common.x", "import runpy"),
        ("agent_pfc.core.common.x", "exec('from agent_pfc import core')"),
        ("agent_pfc.core.common.x", "from builtins import __import__ as load"),
        ("agent_pfc.core.common.x", "__builtins__['__imp' 'ort__']('x')"),
    ],
)
def test_examples_reject_forbidden_imports(module: str, source: str) -> None:
    assert violations(module, source), (module, source)


@pytest.mark.parametrize("namespace", ["agent_pfc.core", "agent_pfc.core.cache"])
def test_examples_reject_a_namespace_with_code(namespace: str) -> None:
    for source in ('"""Doc."""\nX = 1', "from . import common", '"""A."""\n"""B."""'):
        assert violations(namespace, source, True), source
    # A namespace is a package: a plain module of that name is unlisted.
    assert violations(namespace, '"""Doc."""', False)


def test_examples_reject_a_core_import_outside_core_even_if_listed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    table = {"core.common": frozenset({"embeddings"}), "embeddings": frozenset()}
    monkeypatch.setattr(sys.modules[__name__], "ALLOWED", table)
    found = violations("agent_pfc.core.common.x", "import agent_pfc.embeddings")
    assert len(found) == 1
    assert found[0].endswith("which is outside the core")


def test_examples_give_a_module_to_the_longest_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    table = {
        "core.config": frozenset({"core.common"}),
        "core.config.loader": frozenset({"core.utils"}),
    }
    monkeypatch.setattr(sys.modules[__name__], "ALLOWED", table)
    loader = "agent_pfc.core.config.loader"
    assert violations(loader, "import agent_pfc.core.utils") == []
    assert violations(loader, "import agent_pfc.core.common")
    assert violations("agent_pfc.core.config.model", "import agent_pfc.core.utils")


@pytest.mark.parametrize(
    "modules",
    [
        # Between two modules of one package.
        {
            "agent_pfc.a.x": ("from . import y", False),
            "agent_pfc.a.y": ("from agent_pfc.a.x import X", False),
        },
        # Across packages, through a third module.
        {
            "agent_pfc.a.x": ("import agent_pfc.b.y", False),
            "agent_pfc.b.y": ("from ..c import z", False),
            "agent_pfc.c": ("", True),
            "agent_pfc.c.z": ("def f():\n    from agent_pfc.a.x import X", False),
        },
        # Through a package's __init__.
        {
            "agent_pfc.a": ("from .x import X", True),
            "agent_pfc.a.x": ("from agent_pfc.a import Y", False),
        },
        # Through the __init__ that runs when a submodule is imported.
        {
            "agent_pfc.a.x": ("from agent_pfc.b.y import Y", False),
            "agent_pfc.b": ("from agent_pfc.a.x import X", True),
            "agent_pfc.b.y": ("", False),
        },
    ],
)
def test_examples_reject_a_module_cycle_naming_the_modules(modules: Modules) -> None:
    found = cycles(modules)
    assert len(found) == 1
    named = {name for name in modules if name in found[0].split()}
    assert len(named) >= 2, found


@pytest.mark.parametrize(
    ("module", "source"),
    [
        ("agent_pfc.core.common.entries", "from agent_pfc.core.common import failures"),
        ("agent_pfc.core.common.entries", "from .failures import Failure"),
        ("agent_pfc.core.common.entries", "from ..utils import validation"),
        ("agent_pfc.core.common.entries", "from agent_pfc.core import utils"),
        ("agent_pfc.core.utils.validation", "from agent_pfc.core.common import X"),
        ("agent_pfc.core.cache.embedding.disk", "from agent_pfc.core.utils import X"),
        ("agent_pfc.core.client.http", "import agent_pfc.core.activity"),
        ("agent_pfc.core.common.entries", "import dataclasses\nfrom enum import Enum"),
    ],
)
def test_allowed_examples_for_nested_packages_are_accepted(
    module: str, source: str
) -> None:
    assert violations(module, source) == [], (module, source)


def test_allowed_examples_include_namespaces_and_acyclic_modules() -> None:
    assert violations("agent_pfc.core", '"""Doc."""', True) == []
    assert violations("agent_pfc.core.cache", "", True) == []
    # A package's relative import stays inside that package.
    assert violations("agent_pfc.core.common", "from .failures import X", True) == []
    # common and utils may import each other as packages, without a module cycle.
    modules: Modules = {
        "agent_pfc.core.common.failures": ("", False),
        "agent_pfc.core.common.entries": ("from ..utils import validation", False),
        "agent_pfc.core.utils.validation": (
            "from agent_pfc.core.common.failures import Failure",
            False,
        ),
        "agent_pfc.core.common": ('"""Doc."""', True),
        "agent_pfc.core.utils": ('"""Doc."""', True),
    }
    assert cycles(modules) == []
    # An __init__ may re-export modules of its package that import each other.
    package: Modules = {
        "agent_pfc.a": ("from .x import X", True),
        "agent_pfc.a.x": ("from agent_pfc.a.y import Y", False),
        "agent_pfc.a.y": ("", False),
    }
    assert cycles(package) == []
