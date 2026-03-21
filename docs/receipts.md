# Receipts

Language: **English** | [Nederlands](https://tijnschouten.github.io/appie/nl/receipts/)

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

Expected outcome:

```text
AH1... 2026-03-21 14:16:00+00:00 17.78
AH1... 2026-03-07 10:20:00+00:00 24.82
...
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

Expected outcome:

```text
id='AH1...' datetime=... total=17.78 products=[ReceiptProduct(...), ...]
```

Read next: [Shopping Lists](lists.md) for the currently implemented shopping-list operation.
