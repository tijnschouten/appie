# Getting Started

Language: **English** | [Nederlands](https://tijnschouten.github.io/appie/nl/getting-started/)

## Install

```bash
uv add python-appie
```

Or:

```bash
pip install python-appie
```

For local development in this repository:

```bash
uv sync --extra dev
```

## Login

Run:

```bash
uv run appie-login
```

This opens Chrome and captures the AH login redirect code automatically. Tokens are stored in `~/.config/appie/tokens.json`.

Expected outcome:
- a browser window opens for AH login
- after a successful login, tokens are stored locally
- later package usage reuses those tokens automatically

## First request

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        products = await client.products.search("melk", limit=3)
        for product in products:
            print(product)


asyncio.run(main())
```

Expected outcome:

```text
Product(id=...)
Product(id=...)
Product(id=...)
```

Read next: [Authentication](authentication.md) for token storage, refresh behavior, and re-login expectations.
