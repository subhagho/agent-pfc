"""Reading the files of a probe set."""

import hashlib
import json
from pathlib import Path
from typing import Any

from agent_pfc.domain import ProbeSet
from agent_pfc.probes.validation import (
    DATA_FILES,
    OPERATIONS_FILE,
    QUERIES_FILE,
    Located,
    build_probe_set,
)

MANIFEST_FILE = "manifest.json"


def load_probe_set(directory: Path) -> ProbeSet:
    """The validated probe set in `directory`.

    Raises ProbeValidationError listing every unreadable or invalid part.
    """
    failures: list[str] = []
    records: dict[str, list[Located]] = {name: [] for name in DATA_FILES}
    hashes: dict[str, str] = {}
    for name in DATA_FILES:
        content = _read(directory / name, failures)
        if content is None:
            continue
        hashes[name] = hashlib.sha256(content).hexdigest()
        for number, line in enumerate(content.split(b"\n"), start=1):
            if line.strip():
                where = f"{name}:{number}"
                records[name].append((where, _decode(where, line, failures)))
    content = _read(directory / MANIFEST_FILE, failures)
    manifest = None if content is None else _decode(MANIFEST_FILE, content, failures)
    return build_probe_set(
        records[OPERATIONS_FILE], records[QUERIES_FILE], manifest, hashes, failures
    )


def _read(path: Path, failures: list[str]) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError as error:
        failures.append(f"{path.name}: cannot be read: {error.strerror}")
        return None


def _decode(where: str, content: bytes, failures: list[str]) -> Any:
    try:
        return json.loads(content)
    except ValueError as error:
        failures.append(f"{where}: not valid JSON: {error}")
        return None
