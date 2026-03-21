# Snelstart

## Installeren

```bash
uv add python-appie
```

Of:

```bash
pip install python-appie
```

Voor lokale ontwikkeling in deze repository:

```bash
uv sync --extra dev
```

## Inloggen

Voer uit:

```bash
uv run appie-login
```

Dit opent Chrome, vangt automatisch de AH-redirectcode af en slaat tokens op in `~/.config/appie/tokens.json`.

Verwacht resultaat:
- er opent een browservenster voor de AH-login
- na succesvolle login worden tokens lokaal opgeslagen
- later hergebruikt de package die tokens automatisch

## Eerste request

```python
import asyncio

from appie import AHClient


async def main() -> None:
    async with AHClient() as client:
        products = await client.products.search("melk", limit=3)
        for product in products:
            print(product)


asyncio.run(main())
```

Verwacht resultaat:

```text
Product(id=...)
Product(id=...)
Product(id=...)
```
