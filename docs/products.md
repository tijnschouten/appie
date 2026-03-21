# Products

## Search

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
