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
- read the current shopping list via `client.lists.get_list()`
- remove one item via `client.lists.remove_item(item_id)`
- clear the entire list via `client.lists.clear()`
- use `MockAHClient` for local development and tests without touching AH

Example:

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        await client.lists.add_item("Halfvolle melk", quantity=2)
        items = await client.lists.get_list()
        print(items)


asyncio.run(main())
```

Note:
the `ShoppingListItem.id` returned by `get_list()` is an opaque removal key designed for `remove_item(item_id)`. It should be treated as an implementation detail rather than a stable AH server identifier.

### Mocking and downstream tests

- `MockAHClient()` provides an in-memory drop-in client for local development
- `client.mock.calls` and `client.mock.last_call` capture what your code did
- `client.mock.next_response(operation, value)` seeds a one-shot result
- `client.mock.next_error(operation, exc)` seeds a one-shot failure
- `client.mock.set_scenario(operation, delay_ms=..., error=...)` applies persistent delay/error behavior
- `appie.pytest_plugin` provides pytest fixtures for downstream packages

Example:

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        client.mock.next_response("products.search", [])
        products = await client.products.search("melk")
        print(products)
        print(client.mock.last_call)


asyncio.run(main())
```

Expected outcome:

```text
[]
AppieMockCall(operation='products.search', params={'query': 'melk', 'limit': 10}, result=[], error=None)
```

Pytest plugin example:

```python
# tests/conftest.py
pytest_plugins = ["appie.pytest_plugin"]
```

```python
import pytest


@pytest.mark.asyncio
async def test_checkout_uses_expected_query(appie_mock):
    await appie_mock.products.search("melk", limit=3)

    assert appie_mock.mock.last_call is not None
    assert appie_mock.mock.last_call.params == {"query": "melk", "limit": 3}
```

Expected outcome:
- the test runs without touching AH
- the recorded call proves what your code sent into `python-appie`

## API overview

### Main client

- `AHClient()`
- `MockAHClient()`
- `MockAHClient().mock`
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

### Mock helpers

- `client.mock.calls`
- `client.mock.last_call`
- `client.mock.clear_calls()`
- `client.mock.next_response(operation, value)`
- `client.mock.next_error(operation, exc)`
- `client.mock.clear_seeded_responses()`
- `client.mock.set_scenario(operation, delay_ms=0, error=None)`
- `client.mock.clear_scenarios()`

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
- Shopping-list read, add, remove, and clear are implemented against the live main-list endpoint.
- Receipt summaries do not include line items; call `get_pos_receipt()` for a detailed receipt.
- Endpoint discovery for this package is inspired by [gwillem/appie-go](https://github.com/gwillem/appie-go).
