# Bonnen

## Overzichtslijst

`list_all()` en `list_pos_receipts()` geven bonsamenvattingen terug. In die samenvattingen is `products=[]` bewust leeg.

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

Verwacht resultaat:

```text
AH1... 2026-03-21 14:16:00+00:00 17.78
AH1... 2026-03-07 10:20:00+00:00 24.82
...
```

## Gedetailleerde bon

Gebruik `get_pos_receipt()` om de regels van een bon op te halen.

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

Verwacht resultaat:

```text
id='AH1...' datetime=... total=17.78 products=[ReceiptProduct(...), ...]
```
