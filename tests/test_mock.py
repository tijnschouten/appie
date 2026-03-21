from __future__ import annotations

import pytest

from appie import MockAHClient


@pytest.mark.asyncio
async def test_mock_client_product_search():
    async with MockAHClient() as client:
        products = await client.products.search("melk")

    assert products
    assert all("melk" in product.title.lower() for product in products)


@pytest.mark.asyncio
async def test_mock_client_receipt_summary_and_detail():
    async with MockAHClient() as client:
        summaries = await client.receipts.list_all(limit=5)
        detail = await client.receipts.get_pos_receipt(summaries[0].id)

    assert summaries[0].products == []
    assert detail.products


@pytest.mark.asyncio
async def test_mock_client_shopping_list_mutation_flow():
    async with MockAHClient() as client:
        item = await client.lists.add_item("Halfvolle melk", quantity=2, product_id=1525)
        items = await client.lists.get_list()
        await client.lists.remove_item(item.id)
        remaining = await client.lists.get_list()

    assert items[0].description == "Halfvolle melk"
    assert remaining == []


@pytest.mark.asyncio
async def test_mock_client_clear_and_lookup_errors():
    async with MockAHClient() as client:
        await client.lists.add_item("Halfvolle melk")
        await client.lists.clear()

        with pytest.raises(LookupError):
            await client.products.get(999999)

        with pytest.raises(LookupError):
            await client.receipts.get_pos_receipt("missing")

        await client.login()
        await client.aclose()

    assert await client.lists.get_list() == []
