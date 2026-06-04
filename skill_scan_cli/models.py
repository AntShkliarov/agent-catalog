"""Data structures for the artifact catalog."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

Kind = Literal["skill", "agent", "rule"]


@dataclass
class Artifact:
    """A single indexed skill, subagent or rule."""

    kind: Kind
    name: str
    description: str
    path: str  # absolute path: package dir for skills, file for agents/rules
    files: list[str] = field(default_factory=list)  # relative paths inside a skill package
    source_root: str = ""  # e.g. ".agents", ".claude"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Artifact":
        return cls(
            kind=data["kind"],
            name=data["name"],
            description=data.get("description", ""),
            path=data["path"],
            files=list(data.get("files", [])),
            source_root=data.get("source_root", ""),
        )


@dataclass
class Catalog:
    """Indexed artifacts grouped by kind, plus the scanned source path."""

    source: str
    skills: list[Artifact] = field(default_factory=list)
    agents: list[Artifact] = field(default_factory=list)
    rules: list[Artifact] = field(default_factory=list)

    def by_kind(self, kind: Kind) -> list[Artifact]:
        return {"skill": self.skills, "agent": self.agents, "rule": self.rules}[kind]

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "skills": [a.to_dict() for a in self.skills],
            "agents": [a.to_dict() for a in self.agents],
            "rules": [a.to_dict() for a in self.rules],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Catalog":
        return cls(
            source=data.get("source", ""),
            skills=[Artifact.from_dict(a) for a in data.get("skills", [])],
            agents=[Artifact.from_dict(a) for a in data.get("agents", [])],
            rules=[Artifact.from_dict(a) for a in data.get("rules", [])],
        )
