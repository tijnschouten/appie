# Ontwikkeling

## Setup

```bash
uv sync --extra dev
pre-commit install
```

Verwacht resultaat:
- er wordt een lokale virtual environment gemaakt
- ontwikkeldependencies worden geïnstalleerd
- git-hooks worden geïnstalleerd voor volgende commits

## Quality checks

```bash
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
uv run mkdocs build
```

Verwacht resultaat:
- formatting wordt schoon toegepast
- linting slaagt
- type checking slaagt
- tests slagen met coverage
- docs bouwen succesvol

## Pre-commit

Deze repository gebruikt pre-commit hooks voor:

- `ruff format`
- `ruff check`
- `pyright`
- `pytest`
- `mkdocs build`
