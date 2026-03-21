# Shopping Lists

Language: **English** | [Nederlands](https://tijnschouten.github.io/appie/nl/lists/)

## Supported operation

The currently implemented shopping-list operation is `add_item()`.

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        item = await client.lists.add_item("Halfvolle melk", quantity=2)
        print(item)


asyncio.run(main())
```

Expected outcome:

```text
id='item-1' description='Halfvolle melk' quantity=2 product_id=None
```

## Current limitation

`get_list()`, `remove_item()`, and `clear()` are intentionally left unimplemented until their live API shape is confirmed.

Read next: [Mock Client](mock-client.md) for offline development and downstream-package testing.
