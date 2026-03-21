# Receipts

## Summary listing

`list_all()` and `list_pos_receipts()` return receipt summaries. Those summary objects intentionally have `products=[]`.

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        receipts = await client.receipts.list_all(limit=5)
        for receipt in receipts:
            print(receipt.id, receipt.datetime, receipt.total)


asyncio.run(main())
```

## Detailed receipt

Use `get_pos_receipt()` to retrieve line items.

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
