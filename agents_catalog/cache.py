"""Read/write the on-disk catalog cache."""

from __future__ import annotations

import json
from pathlib import Path

from . import scanner
from .models import Artifact, Catalog

CACHE_FILENAME = ".agent-catalog.json"


def cache_path(directory: Path | None = None) -> Path:
    return (directory or Path.cwd()) / CACHE_FILENAME


def write_cache(catalog: Catalog, directory: Path | None = None) -> Path:
    path = cache_path(directory)
    path.write_text(json.dumps(catalog.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def read_cache(directory: Path | None = None) -> Catalog:
    path = cache_path(directory)
    if not path.is_file():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return Catalog.from_dict(data)


def append_skills(new_skills: list[Artifact], directory: Path | None = None) -> Catalog:
    """Additively merge new skills into the cache (deduped by absolute path)."""
    try:
        catalog = read_cache(directory)
    except FileNotFoundError:
        catalog = Catalog(source=str((directory or Path.cwd()).resolve()))
    catalog.skills = scanner.dedup(catalog.skills + new_skills)
    write_cache(catalog, directory)
    return catalog
