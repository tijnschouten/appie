# Development

## Setup

```bash
uv sync --extra dev
pre-commit install
```

## Quality checks

```bash
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
uv run mkdocs build
```

## Pre-commit

This repository uses pre-commit hooks for:

- `ruff format`
- `ruff check`
- `pyright`
- `pytest`
- `mkdocs build`
