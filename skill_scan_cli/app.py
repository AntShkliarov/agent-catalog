"""Typer CLI: index AI-assistant artifacts and copy selected ones into a project."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import questionary
import typer
from rich.console import Console
from rich.table import Table

from . import cache as cache_mod
from . import destinations as dest_mod
from . import scanner
from .installer import install
from .models import Artifact, Catalog, Kind

app = typer.Typer(
    help="Scan a directory for AI-assistant skills, rules and subagents, then copy selected ones into a project.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

_KIND_LABEL = {"skill": "skills", "agent": "agents", "rule": "rules"}


@app.command()
def init(
    target_dir: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Directory to scan for .agents/.cursor/.claude/.github/.codex configs.",
    ),
) -> None:
    """Scan TARGET_DIR and cache discovered skills, subagents and rules."""
    catalog = scanner.scan(target_dir)
    path = cache_mod.write_cache(catalog)

    table = Table(title="Indexed artifacts")
    table.add_column("Kind")
    table.add_column("Count", justify="right")
    table.add_row("Skills", str(len(catalog.skills)))
    table.add_row("Agents", str(len(catalog.agents)))
    table.add_row("Rules", str(len(catalog.rules)))
    console.print(table)
    console.print(f"Cache written to [bold]{path}[/bold]")


def _load_catalog() -> Catalog:
    try:
        return cache_mod.read_cache()
    except FileNotFoundError:
        console.print(
            "[red]No cache found.[/red] Run [bold]skill-scan init <target_dir>[/bold] first."
        )
        raise typer.Exit(code=1)


def _choice_label(a: Artifact) -> str:
    desc = a.description.strip().replace("\n", " ")
    if len(desc) > 100:
        desc = desc[:97] + "..."
    suffix = f" - {desc}" if desc else ""
    return f"[{a.source_root}] {a.name}{suffix}"


def _pick(kind: Kind, target: Path, assistant: Optional[str], overwrite: bool) -> None:
    catalog = _load_catalog()
    artifacts = catalog.by_kind(kind)
    label = _KIND_LABEL[kind]

    if not artifacts:
        console.print(f"[yellow]No {label} indexed.[/yellow]")
        raise typer.Exit(code=0)

    choices = [questionary.Choice(title=_choice_label(a), value=a) for a in artifacts]
    selected: list[Artifact] = (
        questionary.checkbox(
            f"Select {label} to copy (Space to toggle, Enter to confirm):",
            choices=choices,
        ).ask()
        or []
    )
    if not selected:
        console.print("[yellow]Nothing selected.[/yellow]")
        raise typer.Exit(code=0)

    if assistant is None:
        assistant = questionary.select(
            "Copy into which coding assistant?",
            choices=dest_mod.ASSISTANTS,
        ).ask()
    if assistant is None:
        console.print("[yellow]No assistant chosen.[/yellow]")
        raise typer.Exit(code=0)
    if assistant not in dest_mod.ASSISTANTS:
        console.print(f"[red]Unknown assistant '{assistant}'.[/red]")
        raise typer.Exit(code=1)

    dest_dir = dest_mod.destination_dir(target, assistant, kind)
    results = install(selected, dest_dir, overwrite=overwrite)

    for r in results:
        if r.status == "copied":
            console.print(f"[green]copied[/green] {r.artifact.name} -> {r.destination}")
        elif r.status == "skipped":
            console.print(
                f"[yellow]skipped[/yellow] {r.artifact.name} (exists; use --overwrite) -> {r.destination}"
            )
        else:
            console.print(f"[red]missing[/red] {r.artifact.name} (source gone: {r.artifact.path})")


@app.command("pick-skills")
def pick_skills(
    target: Path = typer.Option(
        Path.cwd(), "--target", "-t", resolve_path=True, help="Project root to copy into."
    ),
    assistant: Optional[str] = typer.Option(
        None, "--assistant", "-a", help="Skip the prompt and use this assistant root."
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing destinations."),
) -> None:
    """Interactively select indexed skills and copy them into a project."""
    _pick("skill", target, assistant, overwrite)


@app.command("pick-agents")
def pick_agents(
    target: Path = typer.Option(
        Path.cwd(), "--target", "-t", resolve_path=True, help="Project root to copy into."
    ),
    assistant: Optional[str] = typer.Option(
        None, "--assistant", "-a", help="Skip the prompt and use this assistant root."
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing destinations."),
) -> None:
    """Interactively select indexed subagents and copy them into a project."""
    _pick("agent", target, assistant, overwrite)


@app.command("pick-rules")
def pick_rules(
    target: Path = typer.Option(
        Path.cwd(), "--target", "-t", resolve_path=True, help="Project root to copy into."
    ),
    assistant: Optional[str] = typer.Option(
        None, "--assistant", "-a", help="Skip the prompt and use this assistant root."
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing destinations."),
) -> None:
    """Interactively select indexed rules and copy them into a project."""
    _pick("rule", target, assistant, overwrite)


if __name__ == "__main__":
    app()
