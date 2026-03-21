# Getting Started

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
