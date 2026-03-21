# Mock Client

Language: **English** | [Nederlands](https://tijnschouten.github.io/appie/nl/mock-client/)

## Why use it

`MockAHClient` is intended for local development, demos, and downstream package tests where you want the `python-appie` interface without making live requests to Albert Heijn.

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

Read next: [CLI](cli.md) for the interactive login command used with the real client.
