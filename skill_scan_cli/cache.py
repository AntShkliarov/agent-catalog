"""Read/write the on-disk catalog cache."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Catalog

CACHE_FILENAME = ".skill-scan-cache.json"


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
