"""Mock client implementations for local development and testing."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, TypeVar

from appie.models import Product, Receipt, ReceiptProduct, ShoppingListItem

T = TypeVar("T")
_MISSING = object()


def _default_products() -> list[Product]:
    return [
        Product(
            id=1525,
            title="AH Halfvolle melk",
            brand="AH",
            price=1.29,
            unit_size="1 l",
            image_url="https://example.test/ah-halfvolle-melk.jpg",
        ),
        Product(
            id=441199,
            title="Campina Halfvolle melk voordeelverpakking",
            brand="Campina",
            price=1.99,
            unit_size="1,5 l",
            image_url="https://example.test/campina-halfvolle-melk.jpg",
        ),
        Product(
            id=987654,
            title="AH Pindakaas",
            brand="AH",
            price=2.49,
            unit_size="600 g",
            image_url="https://example.test/ah-pindakaas.jpg",
        ),
    ]


def _default_receipts() -> list[Receipt]:
    return [
        Receipt(
            id="mock-receipt-2",
            datetime=datetime(2026, 3, 21, 14, 16, tzinfo=UTC),
            store_name="Albert Heijn Mockstraat",
            total=17.78,
            products=[
                ReceiptProduct(
                    id=1525,
                    name="AH Halfvolle melk",
                    quantity=2,
                    price_per_unit=1.29,
                    total_price=2.58,
                ),
                ReceiptProduct(
                    id=987654,
                    name="AH Pindakaas",
                    quantity=1,
                    price_per_unit=2.49,
                    total_price=2.49,
                ),
            ],
        ),
        Receipt(
            id="mock-receipt-1",
            datetime=datetime(2026, 3, 7, 10, 20, tzinfo=UTC),
            store_name="Albert Heijn Mockstraat",
            total=24.82,
            products=[
                ReceiptProduct(
                    id=441199,
                    name="Campina Halfvolle melk voordeelverpakking",
                    quantity=2,
                    price_per_unit=1.99,
                    total_price=3.98,
                ),
                ReceiptProduct(
                    id=987654,
                    name="AH Pindakaas",
                    quantity=3,
                    price_per_unit=2.49,
                    total_price=7.47,
                ),
            ],
        ),
    ]


@dataclass(slots=True)
class AppieMockCall:
    """A recorded call made through the mock client."""

    operation: str
    params: dict[str, Any]
    result: Any = None
    error: str | None = None


@dataclass(slots=True)
class AppieMockScenario:
    """Persistent behavior override for a specific mock operation."""

    delay_ms: int = 0
    error: Exception | None = None


@dataclass(slots=True)
class AppieMockController:
    """Programmable controller for the in-process mock client."""

    _calls: list[AppieMockCall] = field(default_factory=list)
    _seeded_responses: dict[str, list[Any]] = field(
        default_factory=lambda: defaultdict(list),
    )
    _seeded_errors: dict[str, list[Exception]] = field(
        default_factory=lambda: defaultdict(list),
    )
    _scenarios: dict[str, AppieMockScenario] = field(default_factory=dict)

    @property
    def calls(self) -> list[AppieMockCall]:
        """Return a snapshot of recorded calls."""
        return list(self._calls)

    @property
    def last_call(self) -> AppieMockCall | None:
        """Return the most recent recorded call, if any."""
        if not self._calls:
            return None
        return self._calls[-1]

    def clear_calls(self) -> None:
        """Drop the current call-capture history."""
        self._calls.clear()

    def next_response(self, operation: str, value: Any) -> None:
        """Seed a one-shot response for the next matching operation."""
        self._seeded_responses[operation].append(deepcopy(value))

    def next_error(self, operation: str, error: Exception) -> None:
        """Seed a one-shot exception for the next matching operation."""
        self._seeded_errors[operation].append(error)

    def clear_seeded_responses(self) -> None:
        """Remove all queued one-shot responses and errors."""
        self._seeded_responses.clear()
        self._seeded_errors.clear()

    def set_scenario(
        self,
        operation: str,
        *,
        delay_ms: int = 0,
        error: Exception | None = None,
    ) -> None:
        """Set a persistent scenario for one operation or all operations."""
        self._scenarios[operation] = AppieMockScenario(delay_ms=delay_ms, error=error)

    def clear_scenarios(self) -> None:
        """Remove all persistent scenarios."""
        self._scenarios.clear()

    async def run(
        self,
        operation: str,
        params: dict[str, Any],
        default_factory: Callable[[], Awaitable[T]],
    ) -> T:
        """Record an operation and apply seeded or scenario-based behavior."""
        call = AppieMockCall(operation=operation, params=deepcopy(params))
        self._calls.append(call)
        scenario = self._scenarios.get(operation) or self._scenarios.get("*")
        await self._maybe_delay(scenario)

        try:
            self._raise_seeded_error(operation)
            self._raise_scenario_error(scenario)
            seeded = self._pop_seeded_response(operation)
            result = seeded if seeded is not _MISSING else await default_factory()
        except Exception as exc:
            call.error = f"{type(exc).__name__}: {exc}"
            raise

        call.result = deepcopy(result)
        return deepcopy(result)

    async def _maybe_delay(self, scenario: AppieMockScenario | None) -> None:
        if scenario is None or scenario.delay_ms <= 0:
            return
        await asyncio.sleep(scenario.delay_ms / 1000)

    def _raise_seeded_error(self, operation: str) -> None:
        errors = self._seeded_errors.get(operation)
        if errors:
            raise errors.pop(0)

    @staticmethod
    def _raise_scenario_error(scenario: AppieMockScenario | None) -> None:
        if scenario is not None and scenario.error is not None:
            raise scenario.error

    def _pop_seeded_response(self, operation: str) -> Any:
        responses = self._seeded_responses.get(operation)
        if not responses:
            return _MISSING
        return responses.pop(0)


class MockProductsAPI:
    """In-memory mock implementation of the products API."""

    def __init__(self, products: list[Product], controller: AppieMockController) -> None:
        """Store the in-memory product catalog and mock controller."""
        self._products = products
        self._mock = controller

    async def search(self, query: str, limit: int = 10) -> list[Product]:
        """Return products whose title or brand contains the query."""

        async def build() -> list[Product]:
            lowered = query.lower()
            matches = [
                product
                for product in self._products
                if lowered in product.title.lower() or lowered in (product.brand or "").lower()
            ]
            return matches[:limit]

        return await self._mock.run(
            "products.search",
            {"query": query, "limit": limit},
            build,
        )

    async def get(self, product_id: int) -> Product:
        """Return a product by ID."""

        async def build() -> Product:
            for product in self._products:
                if product.id == product_id:
                    return product
            raise LookupError(f"Mock product {product_id} was not found.")

        return await self._mock.run("products.get", {"product_id": product_id}, build)


class MockReceiptsAPI:
    """In-memory mock implementation of the receipts API."""

    def __init__(self, receipts: list[Receipt], controller: AppieMockController) -> None:
        """Store the in-memory receipt list and mock controller."""
        self._receipts = receipts
        self._mock = controller

    async def list_pos_receipts(self, limit: int = 50) -> list[Receipt]:
        """Return receipt summaries without line items."""

        async def build() -> list[Receipt]:
            return [self._to_summary(receipt) for receipt in self._receipts[:limit]]

        return await self._mock.run(
            "receipts.list_pos_receipts",
            {"limit": limit},
            build,
        )

    async def get_pos_receipt(self, receipt_id: str) -> Receipt:
        """Return a detailed receipt by ID."""

        async def build() -> Receipt:
            for receipt in self._receipts:
                if receipt.id == receipt_id:
                    return receipt
            raise LookupError(f"Mock receipt {receipt_id} was not found.")

        return await self._mock.run(
            "receipts.get_pos_receipt",
            {"receipt_id": receipt_id},
            build,
        )

    async def list_all(self, limit: int = 50) -> list[Receipt]:
        """Return receipt summaries sorted by datetime descending."""

        async def build() -> list[Receipt]:
            summaries = [self._to_summary(receipt) for receipt in self._receipts[:limit]]
            return sorted(summaries, key=lambda receipt: receipt.datetime, reverse=True)

        return await self._mock.run("receipts.list_all", {"limit": limit}, build)

    @staticmethod
    def _to_summary(receipt: Receipt) -> Receipt:
        return Receipt(
            id=receipt.id,
            datetime=receipt.datetime,
            store_name=receipt.store_name,
            total=receipt.total,
            products=[],
        )


class MockListsAPI:
    """In-memory mock implementation of the shopping-list API."""

    def __init__(
        self,
        items: list[ShoppingListItem],
        controller: AppieMockController,
    ) -> None:
        """Initialize the in-memory shopping list and mock controller."""
        self._items = items
        self._mock = controller

    async def get_list(self) -> list[ShoppingListItem]:
        """Return the current in-memory shopping list."""
        return await self._mock.run("lists.get_list", {}, self._build_get_list)

    async def add_item(
        self,
        description: str,
        quantity: int = 1,
        product_id: int | None = None,
    ) -> ShoppingListItem:
        """Add an item to the in-memory shopping list."""

        async def build() -> ShoppingListItem:
            item = ShoppingListItem(
                id=f"mock-item-{len(self._items) + 1}",
                description=description,
                quantity=quantity,
                product_id=product_id,
            )
            self._items.append(item)
            return item

        return await self._mock.run(
            "lists.add_item",
            {
                "description": description,
                "quantity": quantity,
                "product_id": product_id,
            },
            build,
        )

    async def remove_item(self, item_id: str) -> None:
        """Remove an item from the in-memory shopping list."""

        async def build() -> None:
            self._items = [item for item in self._items if item.id != item_id]
            return None

        await self._mock.run("lists.remove_item", {"item_id": item_id}, build)

    async def clear(self) -> None:
        """Clear the shopping list."""
        await self._mock.run("lists.clear", {}, self._build_clear)

    async def _build_get_list(self) -> list[ShoppingListItem]:
        return self._items

    async def _build_clear(self) -> None:
        self._items.clear()
        return None


class MockAHClient:
    """Drop-in async mock client for local development and tests."""

    def __init__(
        self,
        *,
        products: list[Product] | None = None,
        receipts: list[Receipt] | None = None,
        shopping_list_items: list[ShoppingListItem] | None = None,
    ) -> None:
        """Initialize the mock APIs with optional custom fixture data."""
        product_fixtures = deepcopy(products) if products is not None else _default_products()
        receipt_fixtures = deepcopy(receipts) if receipts is not None else _default_receipts()
        list_fixtures = deepcopy(shopping_list_items) if shopping_list_items is not None else []
        self.mock = AppieMockController()
        self.products = MockProductsAPI(product_fixtures, self.mock)
        self.receipts = MockReceiptsAPI(receipt_fixtures, self.mock)
        self.lists = MockListsAPI(list_fixtures, self.mock)

    async def __aenter__(self) -> MockAHClient:
        """Return the mock client in async context-manager usage."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Allow use in async context-manager blocks."""

    async def aclose(self) -> None:
        """Match the real client interface without external cleanup."""

    async def login(self) -> None:
        """Match the real client interface without external auth."""
