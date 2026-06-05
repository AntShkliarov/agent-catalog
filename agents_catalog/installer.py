"""Copy selected artifacts into a destination folder."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .models import Artifact


@dataclass
class CopyResult:
    artifact: Artifact
    destination: Path
    status: str  # "copied" | "skipped" | "missing"


def _target_for(artifact: Artifact, dest_dir: Path) -> Path:
    src = Path(artifact.path)
    if artifact.kind == "skill":
        return dest_dir / src.name  # package directory
    return dest_dir / src.name  # single file


def install(
    artifacts: list[Artifact],
    dest_dir: Path,
    *,
    overwrite: bool = False,
) -> list[CopyResult]:
    """Copy each artifact into ``dest_dir``; skills as dirs, others as files."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    results: list[CopyResult] = []
    for artifact in artifacts:
        src = Path(artifact.path)
        target = _target_for(artifact, dest_dir)
        if not src.exists():
            results.append(CopyResult(artifact, target, "missing"))
            continue
        if target.exists() and not overwrite:
            results.append(CopyResult(artifact, target, "skipped"))
            continue
        if artifact.kind == "skill":
            shutil.copytree(src, target, dirs_exist_ok=True)
        else:
            shutil.copy2(src, target)
        results.append(CopyResult(artifact, target, "copied"))
    return results
