# Products

Language: **English** | [Nederlands](https://tijnschouten.github.io/appie/nl/products/)

## Search

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        products = await client.products.search("melk", limit=5)
        for product in products:
            print(
                product.title,
                product.price,
                product.original_price,
                product.is_bonus,
                product.is_organic,
            )


asyncio.run(main())
```

Expected outcome:

```text
AH Halfvolle melk 1.29 1.49 True True
Campina Halfvolle melk voordeelverpakking 1.99 None False None
...
```

Product fields now include grocery-planning metadata such as:

- `price`
- `original_price`
- `is_bonus`
- `bonus_label`
- `bonus_start_date`
- `bonus_end_date`
- `is_organic`
- `property_labels`

## Detail

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        product = await client.products.get(1525)
        print(product)


asyncio.run(main())
```

Expected outcome:

```text
id=1525 title='AH Halfvolle melk' brand='AH' price=1.29 original_price=1.49 is_bonus=True is_organic=True ...
```

Read next: [Receipts](receipts.md) for receipt summaries and detailed receipt line items.
