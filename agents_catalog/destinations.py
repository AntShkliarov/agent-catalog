"""Map a chosen coding assistant + artifact kind to a destination subfolder.

The mapping is centralized here because assistant folder conventions differ and
are still evolving; edit the tables below to adjust where artifacts land.
"""

from __future__ import annotations

from pathlib import Path

from .models import Kind

# Selectable target assistants and their root config folder.
ASSISTANTS = [".agents", ".claude", ".cursor", ".codex", ".github"]

# Per-assistant subfolder for each artifact kind, relative to the assistant root.
_SUBFOLDERS: dict[str, dict[Kind, str]] = {
    ".agents": {"skill": "skills", "agent": "agents", "rule": "rules"},
    ".claude": {"skill": "skills", "agent": "agents", "rule": "rules"},
    ".cursor": {"skill": "skills", "agent": "agents", "rule": "rules"},
    ".codex": {"skill": "skills", "agent": "agents", "rule": "rules"},
    ".github": {"skill": "skills", "agent": "agents", "rule": "instructions"},
}


def destination_dir(target_root: Path, assistant: str, kind: Kind) -> Path:
    """Absolute folder where artifacts of ``kind`` are copied for ``assistant``."""
    if assistant not in _SUBFOLDERS:
        raise ValueError(f"Unknown assistant: {assistant}")
    subfolder = _SUBFOLDERS[assistant][kind]
    return (target_root / assistant / subfolder).resolve()
