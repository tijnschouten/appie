# Mockclient

Taal: [English](https://tijnschouten.github.io/appie/mock-client/) | **Nederlands**

## Waarom gebruiken

`MockAHClient` is bedoeld voor lokale ontwikkeling, demo's en tests in downstream packages, zonder live requests naar Albert Heijn te sturen.

De huidige mock-ondersteuning is bedoeld om ontwikkeling in downstream packages soepel te maken:

- stabiel in-memory gedrag voor producten, bonnen en boodschappenlijsten
- call capture zodat je kunt controleren wat je code deed
- one-shot seeded responses voor parser- en edge-case-tests
- persistente delay- en foutscenario's
- pytest-fixtures voor downstream packages

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

## Call capture

Elke mock-API-call wordt vastgelegd via `client.mock`.

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        await client.products.search("melk", limit=3)
        print(client.mock.last_call)


asyncio.run(main())
```

Verwacht resultaat:

```text
AppieMockCall(operation='products.search', params={'query': 'melk', 'limit': 3}, result=[...], error=None)
```

Beschikbare helpers:

- `client.mock.calls`
- `client.mock.last_call`
- `client.mock.clear_calls()`

## Volgende response forceren

Gebruik one-shot seeded responses als je voor precies één call een specifieke returnwaarde wilt afdwingen zonder intern te patchen.

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        client.mock.next_response("products.search", [])

        first = await client.products.search("melk")
        second = await client.products.search("melk")

        print(first)
        print(len(second))


asyncio.run(main())
```

Verwacht resultaat:

```text
[]
2
```

De seeded waarde wordt één keer gebruikt. De tweede call valt terug op de normale in-memory dataset.

## Volgende fout forceren

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        client.mock.next_error("receipts.list_all", RuntimeError("rate limited"))

        try:
            await client.receipts.list_all()
        except RuntimeError as exc:
            print(exc)


asyncio.run(main())
```

Verwacht resultaat:

```text
rate limited
```

## Persistente scenario's

Gebruik scenario's als gedrag moet blijven gelden voor elke matchende call totdat je het wist.

```python
import asyncio

from appie import MockAHClient


async def main() -> None:
    async with MockAHClient() as client:
        client.mock.set_scenario("lists.get_list", delay_ms=250)
        await client.lists.get_list()
        print("done")


asyncio.run(main())
```

Verwacht resultaat:
- de call wordt ongeveer 250 ms vertraagd
- het scenario blijft actief totdat `client.mock.clear_scenarios()` wordt aangeroepen

Je kunt ook een globaal scenario instellen met `operation="*"`.

## Gedrag

- `products.search()` zoekt in een vaste in-memory dataset
- `products.get()` geeft een vast product op ID terug
- `receipts.list_all()` geeft bonsamenvattingen terug met `products=[]`
- `receipts.get_pos_receipt()` geeft een gedetailleerde bon met regelitems terug
- boodschappenlijstacties werken volledig in memory

## Custom fixtures

Je kunt ook je eigen product- en bonfixtures meegeven:

```python
from datetime import UTC, datetime

from appie import MockAHClient
from appie.models import Product, Receipt, ReceiptProduct


client = MockAHClient(
    products=[
        Product(id=1, title="Test product", brand="Mock", price=1.23),
    ],
    receipts=[
        Receipt(
            id="receipt-1",
            datetime=datetime(2026, 1, 1, tzinfo=UTC),
            total=1.23,
            products=[
                ReceiptProduct(
                    id=1,
                    name="Test product",
                    quantity=1,
                    price_per_unit=1.23,
                    total_price=1.23,
                )
            ],
        )
    ],
)
```

Je kunt de boodschappenlijst ook vooraf vullen:

```python
from appie import MockAHClient
from appie.models import ShoppingListItem


client = MockAHClient(
    shopping_list_items=[
        ShoppingListItem(
            id="mock-item-1",
            description="Halfvolle melk",
            quantity=2,
            product_id=1525,
        )
    ]
)
```

Verwacht resultaat:
- `await client.lists.get_list()` geeft direct het ingestelde item terug

## Pytest-plugin

Activeer de plugin in je downstream package:

```python
# tests/conftest.py
pytest_plugins = ["appie.pytest_plugin"]
```

Beschikbare fixtures:

- `appie_mock`: een verse `MockAHClient`
- `appie_mock_controller`: de `client.mock`-controller van dezelfde fixture
- `appie_mock_factory`: een factory voor custom-configureerde mockclients

Voorbeeld:

```python
import pytest


@pytest.mark.asyncio
async def test_checkout_uses_expected_query(appie_mock):
    await appie_mock.products.search("melk", limit=3)

    assert appie_mock.mock.last_call is not None
    assert appie_mock.mock.last_call.params == {"query": "melk", "limit": 3}
```

Verwacht resultaat:
- de test draait volledig offline
- de mock capture laat precies zien hoe je code `python-appie` aanriep

Lees verder: [CLI](cli.md) voor het interactieve logincommando van de echte client.
