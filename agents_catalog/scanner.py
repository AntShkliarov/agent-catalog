"""Scan an assistant-config directory tree for skills, subagents and rules."""

from __future__ import annotations

import re
from pathlib import Path

from .models import Artifact, Catalog

# Config roots scanned for artifacts, relative to the target dir.
CONFIG_ROOTS = [".agents", ".cursor", ".claude", ".github", ".codex"]

SKILL_FILE = "SKILL.md"
RULE_SUFFIXES = {".md", ".mdc"}

# Memory/instruction files indexed as rules, wherever they appear in the tree.
MEMORY_FILES = {"CLAUDE.md", "AGENTS.md"}
# Single rule files indexed at a config root (in addition to rules/ instructions/).
ROOT_RULE_FILES = {".github": ("custom-instructions.md",)}
# Directories skipped while searching for memory files.
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".obsidian"}

# Patterned skill-collection folder names indexed by the additive index-* commands.
SKILL_COLLECTION_DIRS = {"skills"}
PLUGIN_COLLECTION_DIRS = {"claude-plugin", "cursor-plugin"}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter dict, body). Minimal YAML: flat `key: value` pairs."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    fm: dict[str, str] = {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
        m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", lines[i])
        if m:
            key, value = m.group(1).strip(), m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fm[key] = value
    if end is None:
        return {}, text
    body = "\n".join(lines[end + 1 :])
    return fm, body


def _first_heading(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def _description_from_body(body: str, max_lines: int = 5) -> str:
    collected: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        collected.append(stripped)
        if len(collected) >= max_lines:
            break
    return " ".join(collected)


def _list_package_files(package_dir: Path) -> list[str]:
    files: list[str] = []
    for p in sorted(package_dir.rglob("*")):
        if p.is_file():
            files.append(str(p.relative_to(package_dir)))
    return files


def _skill_artifact(skill_md: Path, root_name: str) -> Artifact:
    package_dir = skill_md.parent
    fm, body = parse_frontmatter(_read_text(skill_md))
    name = fm.get("name") or package_dir.name
    description = fm.get("description") or _first_heading(body) or _description_from_body(body)
    return Artifact(
        kind="skill",
        name=name,
        description=description,
        path=str(package_dir.resolve()),
        files=_list_package_files(package_dir),
        source_root=root_name,
    )


def _agent_artifact(file: Path, root_name: str) -> Artifact:
    fm, body = parse_frontmatter(_read_text(file))
    name = fm.get("name") or file.stem
    description = fm.get("description") or _first_heading(body) or _description_from_body(body)
    return Artifact(
        kind="agent",
        name=name,
        description=description,
        path=str(file.resolve()),
        source_root=root_name,
    )


def _rule_artifact(file: Path, root_name: str) -> Artifact:
    fm, body = parse_frontmatter(_read_text(file))
    name = fm.get("name") or file.stem
    description = fm.get("description") or _description_from_body(body)
    return Artifact(
        kind="rule",
        name=name,
        description=description,
        path=str(file.resolve()),
        source_root=root_name,
    )


def _scan_root(root: Path, root_name: str) -> tuple[list[Artifact], list[Artifact], list[Artifact]]:
    skills: list[Artifact] = []
    agents: list[Artifact] = []
    rules: list[Artifact] = []

    skill_dirs: list[Path] = []
    for skill_md in root.rglob(SKILL_FILE):
        if skill_md.is_file():
            skills.append(_skill_artifact(skill_md, root_name))
            skill_dirs.append(skill_md.parent.resolve())

    def inside_skill(p: Path) -> bool:
        rp = p.resolve()
        return any(rp == d or d in rp.parents for d in skill_dirs)

    for agents_dir in root.rglob("agents"):
        if not agents_dir.is_dir() or inside_skill(agents_dir):
            continue
        for file in sorted(agents_dir.glob("*.md")):
            if file.is_file():
                agents.append(_agent_artifact(file, root_name))

    rule_dirs = list(root.rglob("rules")) + list(root.rglob("instructions"))
    for rules_dir in rule_dirs:
        if not rules_dir.is_dir() or inside_skill(rules_dir):
            continue
        for file in sorted(rules_dir.rglob("*")):
            if file.is_file() and file.suffix in RULE_SUFFIXES and not inside_skill(file):
                rules.append(_rule_artifact(file, root_name))

    for filename in ROOT_RULE_FILES.get(root_name, ()):
        candidate = root / filename
        if candidate.is_file():
            rules.append(_rule_artifact(candidate, root_name))

    return skills, agents, rules


def _scan_memory_files(target_dir: Path) -> list[Artifact]:
    """Index CLAUDE.md / AGENTS.md anywhere under target_dir as rules."""
    rules: list[Artifact] = []
    for path in sorted(target_dir.rglob("*")):
        if not path.is_file() or path.name not in MEMORY_FILES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(target_dir).parts):
            continue
        rules.append(_rule_artifact(path, "."))
    return rules


def scan_collections(target_dir: Path, folder_names: set[str]) -> list[Artifact]:
    """Find dirs named in folder_names anywhere under target_dir; index each
    immediate child <skill>/ that contains SKILL.md."""
    target_dir = target_dir.resolve()
    out: list[Artifact] = []
    for coll in sorted(target_dir.rglob("*")):
        if not coll.is_dir() or coll.name not in folder_names:
            continue
        if any(p in SKIP_DIRS for p in coll.relative_to(target_dir).parts):
            continue
        for child in sorted(coll.iterdir()):
            skill_md = child / SKILL_FILE
            if child.is_dir() and skill_md.is_file():
                out.append(_skill_artifact(skill_md, coll.name))
    return out


def dedup(artifacts: list[Artifact]) -> list[Artifact]:
    seen: set[str] = set()
    out: list[Artifact] = []
    for a in artifacts:
        if a.path in seen:
            continue
        seen.add(a.path)
        out.append(a)
    return out


def scan(target_dir: Path) -> Catalog:
    """Index skills, subagents and rules under the config roots of ``target_dir``."""
    target_dir = target_dir.resolve()
    catalog = Catalog(source=str(target_dir))
    for root_name in CONFIG_ROOTS:
        root = target_dir / root_name
        if not root.is_dir():
            continue
        skills, agents, rules = _scan_root(root, root_name)
        catalog.skills.extend(skills)
        catalog.agents.extend(agents)
        catalog.rules.extend(rules)

    catalog.rules.extend(_scan_memory_files(target_dir))

    catalog.skills = dedup(catalog.skills)
    catalog.agents = dedup(catalog.agents)
    catalog.rules = dedup(catalog.rules)
    return catalog
