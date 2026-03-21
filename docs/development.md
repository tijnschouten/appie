# Development

## Setup

```bash
uv sync --extra dev
pre-commit install
```

Expected outcome:
- a local virtual environment is created
- development dependencies are installed
- git hooks are installed for future commits

## Quality checks

```bash
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
uv run mkdocs build
```

Expected outcome:
- formatting is applied cleanly
- linting passes
- type checking passes
- tests pass with coverage
- docs build successfully

## Pre-commit

This repository uses pre-commit hooks for:

- `ruff format`
- `ruff check`
- `pyright`
- `pytest`
- `mkdocs build`
