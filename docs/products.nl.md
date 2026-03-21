# Producten

## Zoeken

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        products = await client.products.search("melk", limit=5)
        for product in products:
            print(product.title, product.price)


asyncio.run(main())
```

Verwacht resultaat:

```text
AH Halfvolle melk 1.29
Campina Halfvolle melk voordeelverpakking 1.99
...
```

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

Verwacht resultaat:

```text
id=1525 title='AH Halfvolle melk' brand='AH' price=1.29 ...
```
