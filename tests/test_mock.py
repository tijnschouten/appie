from __future__ import annotations

import asyncio

import pytest

from appie import MockAHClient
from appie.mock import AppieMockCall
from appie.pytest_plugin import (
    build_appie_mock,
    build_appie_mock_controller,
    build_appie_mock_factory,
)


@pytest.mark.asyncio
async def test_mock_client_product_search_captures_calls():
    async with MockAHClient() as client:
        products = await client.products.search("melk")

    assert products
    assert all("melk" in product.title.lower() for product in products)
    assert products[0].is_bonus is True
    assert products[0].is_organic is True
    assert products[0].bonus_label == "2e halve prijs"
    assert client.mock.last_call == AppieMockCall(
        operation="products.search",
        params={"query": "melk", "limit": 10},
        result=products,
        error=None,
    )


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


@pytest.mark.asyncio
async def test_mock_client_next_response_is_consumed_once():
    async with MockAHClient() as client:
        client.mock.next_response("products.search", [])
        first = await client.products.search("melk")
        second = await client.products.search("melk")

    assert first == []
    assert second
    assert len(client.mock.calls) == 2


@pytest.mark.asyncio
async def test_mock_client_next_error_records_failure():
    async with MockAHClient() as client:
        client.mock.next_error("receipts.list_all", RuntimeError("rate limited"))

        with pytest.raises(RuntimeError, match="rate limited"):
            await client.receipts.list_all()

    assert client.mock.last_call is not None
    assert client.mock.last_call.error == "RuntimeError: rate limited"


@pytest.mark.asyncio
async def test_mock_client_scenario_delay(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    async with MockAHClient() as client:
        client.mock.set_scenario("lists.get_list", delay_ms=250)
        await client.lists.get_list()

    assert slept == [0.25]


@pytest.mark.asyncio
async def test_mock_client_global_scenario_error():
    async with MockAHClient() as client:
        client.mock.set_scenario("*", error=RuntimeError("mock outage"))

        with pytest.raises(RuntimeError, match="mock outage"):
            await client.products.search("melk")

    assert client.mock.last_call is not None
    assert client.mock.last_call.operation == "products.search"


def test_pytest_plugin_fixtures_expose_mock_client():
    client = build_appie_mock()
    controller = build_appie_mock_controller(client)
    factory = build_appie_mock_factory()

    assert isinstance(client, MockAHClient)
    assert controller is client.mock
    assert factory is MockAHClient
