# python-appie

`python-appie` is an unofficial async Python client for the Albert Heijn API.

[Full documentation](https://tijnschouten.github.io/appie/) is available in English and Dutch. The source for the docs lives in [`docs/`](/Users/tijnschouten/repos/personal/appie/docs) and is built from [`mkdocs.yml`](/Users/tijnschouten/repos/personal/appie/mkdocs.yml).

Releases are intended to publish to PyPI as `python-appie` from version tags via GitHub Actions.

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
pre-commit install
```

## Quick start

Authenticate once:

```bash
uv run appie-login
```

This opens Chrome for an interactive AH login and captures the OAuth redirect code automatically. If automatic capture cannot start, the CLI falls back to asking for the redirect URL or raw code manually.

Then use the client:

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

Tokens are stored in `~/.config/appie/tokens.json` and refreshed automatically when they are close to expiring.

## Features

### Authentication

- `appie-login` CLI for browser-based login
- automatic code capture from the AH redirect flow
- token persistence in `~/.config/appie/tokens.json`
- automatic token refresh using the stored refresh token

### Products

- search products via `client.products.search(query, limit=10)`
- fetch a single product via `client.products.get(product_id)`

Example:

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        product = await client.products.get(1525)
        print(product)


asyncio.run(main())
```

### Receipts

- list in-store POS receipt summaries via `client.receipts.list_all(limit=50)`
- fetch a receipt with line items via `client.receipts.get_pos_receipt(receipt_id)`

Important:
`list_all()` and `list_pos_receipts()` return receipt summaries. In those results, `products` is intentionally empty.
To retrieve line items, call `get_pos_receipt()` with a receipt ID from the summary list.

Example:

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        receipts = await client.receipts.list_all(limit=5)
        detailed = await client.receipts.get_pos_receipt(receipts[0].id)
        print(detailed)


asyncio.run(main())
```

### Shopping lists

- add an item via `client.lists.add_item(description, quantity=1, product_id=None)`
- use `MockAHClient` for local development and tests without touching AH

Example:

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        item = await client.lists.add_item("Halfvolle melk", quantity=2)
        print(item)


asyncio.run(main())
```

Current limitation:
shopping-list add is implemented, but `get_list()`, `remove_item()`, and `clear()` still raise `NotImplementedError` until their live API shape is confirmed.

## API overview

### Main client

- `AHClient()`
- `MockAHClient()`
- `await client.login()`
- `await client.graphql(query, variables=None)`

### Auth client

- `AHAuthClient.get_anonymous_token()`
- `AHAuthClient.login_with_code(code)`
- `AHAuthClient.refresh_token(refresh_token)`

### Sub-APIs

- `client.products.search(query, limit=10)`
- `client.products.get(product_id)`
- `client.receipts.list_pos_receipts(limit=50)`
- `client.receipts.list_all(limit=50)`
- `client.receipts.get_pos_receipt(receipt_id)`
- `client.lists.add_item(description, quantity=1, product_id=None)`
- `client.lists.get_list()`
- `client.lists.remove_item(item_id)`
- `client.lists.clear()`

## Development

Run checks locally:

```bash
uv run ruff format .
uv run --extra dev ruff check .
uv run --extra dev pyright
uv run --extra dev pytest
uv run --extra dev mkdocs build --strict
```

## Notes

- This client is unofficial and may break when Albert Heijn changes its backend.
- Receipt support currently covers in-store POS receipts.
- Shopping-list support only implements the verified add-item mutation; other operations raise explicit `NotImplementedError` until their GraphQL shape is confirmed.
- Receipt summaries do not include line items; call `get_pos_receipt()` for a detailed receipt.
- Endpoint discovery for this package is inspired by [gwillem/appie-go](https://github.com/gwillem/appie-go).
