# Boodschappenlijsten

## Ondersteunde actie

De momenteel geïmplementeerde boodschappenlijstactie is `add_item()`.

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        item = await client.lists.add_item("Halfvolle melk", quantity=2)
        print(item)


asyncio.run(main())
```

Verwacht resultaat:

```text
id='item-1' description='Halfvolle melk' quantity=2 product_id=None
```

## Huidige beperking

`get_list()`, `remove_item()` en `clear()` zijn bewust nog niet geïmplementeerd totdat de live API-vorm bevestigd is.
