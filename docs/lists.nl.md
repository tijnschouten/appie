# Boodschappenlijsten

Taal: [English](https://tijnschouten.github.io/appie/lists/) | **Nederlands**

## Ondersteunde acties

De boodschappenlijst-API ondersteunt nu:

- `add_item()`
- `get_list()`
- `remove_item()`
- `clear()`

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

Verwacht resultaat:

```text
[ShoppingListItem(id='prd:1525:AH%20Halfvolle%20melk', description='AH Halfvolle melk', quantity=2, product_id=1525)]
```

## Eén item verwijderen

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        items = await client.lists.get_list()
        if items:
            await client.lists.remove_item(items[0].id)


asyncio.run(main())
```

Verwacht resultaat:
- het eerste item uit de huidige boodschappenlijst wordt verwijderd

## Lijst leegmaken

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        await client.lists.clear()


asyncio.run(main())
```

Verwacht resultaat:
- alle huidige boodschappenlijstitems worden verwijderd

## Opmerking over item-ID's

De `ShoppingListItem.id` uit `get_list()` is een opaque removal key die bedoeld is om terug te geven aan `remove_item(item_id)`. Zie dit niet als een stabiele server-ID van AH.

Lees verder: [Mockclient](mock-client.md) voor offline ontwikkeling en tests in downstream packages.
