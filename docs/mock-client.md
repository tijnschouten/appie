# Mock Client

Language: **English** | [Nederlands](https://tijnschouten.github.io/appie/nl/mock-client/)

## Why use it

`MockAHClient` is intended for local development, demos, and downstream package tests where you want the `python-appie` interface without making live requests to Albert Heijn.

The current mock support is designed to make downstream development smooth:

- stable in-memory product, receipt, and shopping-list behavior
- call capture so you can assert what your code did
- one-shot seeded responses for parser and edge-case tests
- persistent delay and error scenarios
- pytest fixtures for downstream packages

This helps when you want to:

- develop UI or business logic against the package API
- write tests in packages that depend on `python-appie`
- avoid unnecessary traffic to AH while iterating locally

## Example

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        products = await client.products.search("melk")
        receipts = await client.receipts.list_all(limit=5)
        detail = await client.receipts.get_pos_receipt(receipts[0].id)
        item = await client.lists.add_item("Halfvolle melk", quantity=2)

        print(products[0])
        print(detail)
        print(item)


asyncio.run(main())
```

Expected outcome:
- product search returns fixed in-memory products
- receipt listing and detail work without calling AH
- shopping-list mutations work entirely in memory

## Call capture

Every mock API call is recorded through `client.mock`.

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        await client.products.search("melk", limit=3)
        print(client.mock.last_call)


asyncio.run(main())
```

Expected outcome:

```text
AppieMockCall(operation='products.search', params={'query': 'melk', 'limit': 3}, result=[...], error=None)
```

Available helpers:

- `client.mock.calls`
- `client.mock.last_call`
- `client.mock.clear_calls()`

## Seed the next response

Use one-shot seeded responses when you want to force a very specific return value without patching internals.

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        client.mock.next_response("products.search", [])

        first = await client.products.search("melk")
        second = await client.products.search("melk")

        print(first)
        print(len(second))


asyncio.run(main())
```

Expected outcome:

```text
[]
2
```

The seeded value is consumed once. The second call falls back to the normal in-memory dataset.

## Seed the next error

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        client.mock.next_error("receipts.list_all", RuntimeError("rate limited"))

        try:
            await client.receipts.list_all()
        except RuntimeError as exc:
            print(exc)


asyncio.run(main())
```

Expected outcome:

```text
rate limited
```

## Persistent scenarios

Use scenarios when you want behavior to apply to every matching call until you clear it.

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        client.mock.set_scenario("lists.get_list", delay_ms=250)
        await client.lists.get_list()
        print("done")


asyncio.run(main())
```

Expected outcome:
- the call is delayed by roughly 250 ms
- the scenario remains active until `client.mock.clear_scenarios()` is called

You can also set a global scenario with `operation="*"`.

## Behavior

- `products.search()` searches a fixed in-memory dataset
- `products.get()` returns a fixed product by ID
- `receipts.list_all()` returns receipt summaries with `products=[]`
- `receipts.get_pos_receipt()` returns a detailed receipt with line items
- shopping-list operations are fully in-memory

## Custom fixtures

You can also inject your own product and receipt fixtures:

```python
from datetime import UTC, datetime

from appie import MockAHClient
from appie.models import Product, Receipt, ReceiptProduct


client = MockAHClient(
    products=[
        Product(id=1, title="Test product", brand="Mock", price=1.23),
    ],
    receipts=[
        Receipt(
            id="receipt-1",
            datetime=datetime(2026, 1, 1, tzinfo=UTC),
            total=1.23,
            products=[
                ReceiptProduct(
                    id=1,
                    name="Test product",
                    quantity=1,
                    price_per_unit=1.23,
                    total_price=1.23,
                )
            ],
        )
    ],
)
```

You can also pre-populate the shopping list:

```python
from appie import MockAHClient
from appie.models import ShoppingListItem


client = MockAHClient(
    shopping_list_items=[
        ShoppingListItem(
            id="mock-item-1",
            description="Halfvolle melk",
            quantity=2,
            product_id=1525,
        )
    ]
)
```

Expected outcome:
- `await client.lists.get_list()` returns the injected item immediately

## Pytest plugin

Enable the plugin in your downstream package:

```python
# tests/conftest.py
pytest_plugins = ["appie.pytest_plugin"]
```

Available fixtures:

- `appie_mock`: a fresh `MockAHClient`
- `appie_mock_controller`: the `client.mock` controller for the same fixture
- `appie_mock_factory`: a factory for creating custom-configured mock clients

Example:

```python
import pytest


@pytest.mark.asyncio
async def test_checkout_uses_expected_query(appie_mock):
    await appie_mock.products.search("melk", limit=3)

    assert appie_mock.mock.last_call is not None
    assert appie_mock.mock.last_call.params == {"query": "melk", "limit": 3}
```

Expected outcome:
- the test runs fully offline
- the mock capture shows exactly how your code called `python-appie`

Read next: [CLI](cli.md) for the interactive login command used with the real client.
