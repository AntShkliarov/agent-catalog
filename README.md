# skill-scan-cli

A Typer CLI that scans a directory for AI-assistant artifacts (skills, rules, subagents), caches them, and lets you interactively copy selected ones into a chosen coding assistant's folder layout.

## Install / run

This is a [uv](https://docs.astral.sh/uv/) project.

```bash
uv sync
uv run skill-scan --help
```

## Commands

### `init <target_dir>`

Scans `target_dir` for the config roots `.agents/`, `.cursor/`, `.claude/`, `.github/`, `.codex/` and indexes:

- Skills: any folder containing `SKILL.md` (the whole package, including `assets/`, `references/`, `examples/`).
- Subagents: `*.md` files directly under an `agents/` folder.
- Rules: `*.md` / `*.mdc` under `rules/` and (recursively) `instructions/` (e.g. `.github/instructions/**/*.instructions.md`), `.github/custom-instructions.md`, plus any `CLAUDE.md` / `AGENTS.md` memory files anywhere under the target (excluding `.git`, `.venv`, `node_modules`, etc.).

Names and descriptions come from YAML frontmatter (`name`, `description`); rules fall back to the filename plus the first few lines. Results are written to `.skill-scan-cache.json` in the current directory.

```bash
uv run skill-scan init /path/to/source
```

### `pick-skills` / `pick-agents` / `pick-rules`

Loads the cache, shows an interactive multi-select (Arrows to move, `<Space>` to toggle, `Enter` to confirm), asks which coding assistant to target, and copies the selected artifacts into that assistant's folder.

```bash
uv run skill-scan pick-skills                 # copy into ./ (cwd)
uv run skill-scan pick-rules --target ./proj  # copy into another project root
uv run skill-scan pick-agents --assistant .claude --overwrite
```

Options:

- `--target, -t` — project root to copy into (default: cwd).
- `--assistant, -a` — skip the assistant prompt (`.agents`, `.claude`, `.cursor`, `.codex`, `.github`).
- `--overwrite` — overwrite existing destinations (otherwise they are skipped).

## Destination mapping

Per-assistant destinations are defined in [`skill_scan_cli/destinations.py`](skill_scan_cli/destinations.py):

| Kind   | Default subfolder                                  |
| ------ | -------------------------------------------------- |
| skill  | `<assistant>/skills/<name>/`                       |
| agent  | `<assistant>/agents/<file>`                        |
| rule   | `<assistant>/rules/<file>` (`.github` -> `instructions/`) |

These are sensible defaults; edit the tables in `destinations.py` to match evolving conventions.
