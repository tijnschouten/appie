# Mockclient

## Waarom gebruiken

`MockAHClient` is bedoeld voor lokale ontwikkeling, demo's en tests in downstream packages, zonder live requests naar Albert Heijn te sturen.

Handig voor:

- UI- of businesslogic bouwen tegen de `python-appie`-interface
- tests schrijven in packages die van `python-appie` afhankelijk zijn
- itereren zonder onnodig verkeer naar AH te sturen

## Voorbeeld

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

Verwacht resultaat:
- productzoekopdrachten geven vaste in-memory producten terug
- bonoverzicht en bondetail werken zonder live AH-calls
- boodschappenlijstmutaties werken volledig in memory
