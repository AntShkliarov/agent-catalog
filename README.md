# agent-catalog

A Typer CLI that scans a directory for AI-assistant artifacts (skills, rules, subagents), caches them, and lets you interactively copy selected ones into a chosen coding assistant's folder layout.

## Install / run

This is a [uv](https://docs.astral.sh/uv/) project.

```bash
uv sync
uv run agent-catalog --help
```

## Commands

### `init <target_dir>`

Scans `target_dir` for the config roots `.agents/`, `.cursor/`, `.claude/`, `.github/`, `.codex/` and indexes:

- Skills: any folder containing `SKILL.md` (the whole package, including `assets/`, `references/`, `examples/`).
- Subagents: `*.md` files directly under an `agents/` folder.
- Rules: `*.md` / `*.mdc` under `rules/` and (recursively) `instructions/` (e.g. `.github/instructions/**/*.instructions.md`), `.github/custom-instructions.md`, plus any `CLAUDE.md` / `AGENTS.md` memory files anywhere under the target (excluding `.git`, `.venv`, `node_modules`, etc.).

Names and descriptions come from YAML frontmatter (`name`, `description`); rules fall back to the filename plus the first few lines. Results are written to `.agent-catalog.json` in the current directory.

```bash
uv run agent-catalog init /path/to/source
```

### `index-skills <target_dir>` / `index-plugins <target_dir>`

Additive scans for patterned skill collections, discovered recursively anywhere under `target_dir`. Each immediate `<skill>/` subfolder containing a `SKILL.md` is indexed and **appended** to the existing `.agent-catalog.json` (deduped by absolute path, so re-runs and overlap with `init` are safe).

- `index-skills` — folders named `skills/` (`skills/<skill>/`).
- `index-plugins` — folders named `claude-plugin/` and `cursor-plugin/` (`claude-plugin/<skill>/`, `cursor-plugin/<skill>/`).

```bash
uv run agent-catalog index-skills /path/to/source
uv run agent-catalog index-plugins /path/to/source
```

### `pick-skills` / `pick-agents` / `pick-rules`

Loads the cache and opens on the full catalog as an interactive multi-select (Arrows to move, type to filter live, `<Space>` to toggle, `Enter` to confirm), asks which coding assistant to target, and copies the selected artifacts into that assistant's folder.

```bash
uv run agent-catalog pick-skills                 # copy into ./ (cwd)
uv run agent-catalog pick-rules --target ./proj  # copy into another project root
uv run agent-catalog pick-agents --assistant .claude --overwrite
```

### `pick-skills:filter` / `pick-agents:filter` / `pick-rules:filter`

Same as the base pickers, but pre-narrow the catalog by a filter TERM (case-insensitive substring on the artifact **name**) before the picker opens — handy for large catalogs. If TERM is omitted you are prompted for it. Live type-to-filter still applies on top.

```bash
uv run agent-catalog pick-skills:filter wiki     # only skills whose name contains "wiki"
uv run agent-catalog pick-rules:filter           # prompts for a filter term
```

Options (all pick commands):

- `--target, -t` — project root to copy into (default: cwd).
- `--assistant, -a` — the target coding assistant whose folder convention the selected artifacts are copied into (one of `.agents`, `.claude`, `.cursor`, `.codex`, `.github`). This selects the destination root, combined with the per-kind subfolder to form the copy destination (e.g. `<target>/.claude/skills/<name>/`). It affects where files land only, not what is scanned or indexed. If omitted, the command asks you to choose one before copying.
- `--overwrite` — replace artifacts that already exist at the destination. Skills (directory packages) are merged over the existing folder, overwriting overlapping files but leaving any extra files in place; agents/rules (single files) are replaced. Without it, existing targets are left untouched and reported as `skipped`. Sources that no longer exist are reported as `missing` regardless of this flag.

## Destination mapping

Per-assistant destinations are defined in [`agents_catalog/destinations.py`](agents_catalog/destinations.py):

| Kind   | Default subfolder                                  |
| ------ | -------------------------------------------------- |
| skill  | `<assistant>/skills/<name>/`                       |
| agent  | `<assistant>/agents/<file>`                        |
| rule   | `<assistant>/rules/<file>` (`.github` -> `instructions/`) |

These are sensible defaults; edit the tables in `destinations.py` to match evolving conventions.
