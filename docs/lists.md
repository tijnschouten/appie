# Shopping Lists

Language: **English** | [Nederlands](https://tijnschouten.github.io/appie/nl/lists/)

## Supported operations

The shopping-list API currently supports:

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

Expected outcome:

```text
[ShoppingListItem(id='prd:1525:AH%20Halfvolle%20melk', description='AH Halfvolle melk', quantity=2, product_id=1525)]
```

## Remove one item

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

Expected outcome:
- the first item from the current shopping list is removed

## Clear the list

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        await client.lists.clear()


asyncio.run(main())
```

Expected outcome:
- all current shopping-list items are removed

## Note on item IDs

The `ShoppingListItem.id` returned by `get_list()` is an opaque removal key intended to be passed back into `remove_item(item_id)`. It should not be treated as a stable AH server-side identifier.

Read next: [Mock Client](mock-client.md) for offline development and downstream-package testing.
