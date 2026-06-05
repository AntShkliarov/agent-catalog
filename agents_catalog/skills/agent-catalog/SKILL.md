---
name: agent-catalog
description: Manage a catalog of AI-assistant skills, subagents and rules with the agent-catalog CLI, and install selected ones into the current workspace or the global agent skills. Use when the user wants to catalog, index, search, find, add, or install skills/subagents/rules, or set up reusable agent assets in a workspace.
---

# agent-catalog

Drive the `agent-catalog` CLI to build a catalog of reusable AI-assistant assets (skills, subagents, rules) and install the right ones into the workspace you operate in or into the global agent skills.

## Prerequisite

The `agent-catalog` command. From the CLI repo: `uv run agent-catalog ...`. Installed globally: `pip install agent-catalog-cli`, then `agent-catalog ...`. Examples below use the bare command.

## Build / refresh the catalog (non-interactive)

These commands take a directory and write/append `.agent-catalog.json` in the current directory. Safe to run unattended.

- `agent-catalog init <dir>` — scan the config roots `.agents/ .cursor/ .claude/ .github/ .codex/` under `<dir>` (overwrites the cache).
- `agent-catalog add-skills <dir>` — additively index `skills/<skill>/` packages found anywhere under `<dir>`.
- `agent-catalog add-plugins <dir>` — additively index `claude-plugin/<skill>/` and `cursor-plugin/<skill>/` packages.

`add-*` append and dedupe by absolute path, so re-runs and overlap with `init` are safe.

## Discover / search (read the cache directly)

To list or filter what is available before installing, read `.agent-catalog.json`. It has `skills`, `agents`, `rules` arrays; each entry carries `name`, `description`, `path`, `source_root`. Filter on `name`/`description` to pick targets — no extra tooling needed.

## Install into the workspace or globally (via CLI)

Installation is done with the `pick-*` commands. `--target` chooses the root and `--assistant` the folder convention; together they decide where files land (`<target>/<assistant>/skills/<name>/`).

- Current workspace: `agent-catalog pick-skills --target . --assistant .cursor` → `./.cursor/skills/<name>/`
- Global agent skills: `agent-catalog pick-skills --target ~ --assistant .cursor` → `~/.cursor/skills/<name>/`
- Pre-filter a large catalog: `agent-catalog pick-skills:filter <term> --target . --assistant .cursor`
- Subagents and rules: same flags with `pick-agents` / `pick-rules`.
- Add `--overwrite` to replace assets that already exist at the destination.

`pick-*` opens an interactive checkbox (requires a TTY): run the command, then the human selects entries (type to filter, Space to toggle, Enter to confirm) and chooses the assistant if `--assistant` was omitted. `init` and `add-*` need no interaction.

## Install this skill

This management skill ships inside the package. Install it directly (non-interactive):

- Workspace: `agent-catalog install-skill --target . --assistant .cursor` → `./.cursor/skills/agent-catalog/`
- Global: `agent-catalog install-skill --target ~ --assistant .cursor` → `~/.cursor/skills/agent-catalog/`

Add `--overwrite` to refresh an existing copy.

## When not to use

- One-off file copies of a single known path — just copy it.
- Authoring or editing skill contents — use `create-skill`. This skill catalogs and installs existing assets; it does not write them.
