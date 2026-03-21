"""Mock client implementations for local development and testing."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

from appie.models import Product, Receipt, ReceiptProduct, ShoppingListItem


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


class MockProductsAPI:
    """In-memory mock implementation of the products API."""

    def __init__(self, products: list[Product]) -> None:
        """Store the in-memory product catalog."""
        self._products = products

    async def search(self, query: str, limit: int = 10) -> list[Product]:
        """Return products whose title or brand contains the query."""
        lowered = query.lower()
        matches = [
            product
            for product in self._products
            if lowered in product.title.lower() or lowered in (product.brand or "").lower()
        ]
        return matches[:limit]

    async def get(self, product_id: int) -> Product:
        """Return a product by ID."""
        for product in self._products:
            if product.id == product_id:
                return product
        raise LookupError(f"Mock product {product_id} was not found.")


class MockReceiptsAPI:
    """In-memory mock implementation of the receipts API."""

    def __init__(self, receipts: list[Receipt]) -> None:
        """Store the in-memory receipt list."""
        self._receipts = receipts

    async def list_pos_receipts(self, limit: int = 50) -> list[Receipt]:
        """Return receipt summaries without line items."""
        return [self._to_summary(receipt) for receipt in self._receipts[:limit]]

    async def get_pos_receipt(self, receipt_id: str) -> Receipt:
        """Return a detailed receipt by ID."""
        for receipt in self._receipts:
            if receipt.id == receipt_id:
                return receipt.model_copy(deep=True)
        raise LookupError(f"Mock receipt {receipt_id} was not found.")

    async def list_all(self, limit: int = 50) -> list[Receipt]:
        """Return receipt summaries sorted by datetime descending."""
        summaries = await self.list_pos_receipts(limit=limit)
        return sorted(summaries, key=lambda receipt: receipt.datetime, reverse=True)

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

    def __init__(self) -> None:
        """Initialize an empty in-memory shopping list."""
        self._items: list[ShoppingListItem] = []

    async def get_list(self) -> list[ShoppingListItem]:
        """Return the current in-memory shopping list."""
        return [item.model_copy(deep=True) for item in self._items]

    async def add_item(
        self,
        description: str,
        quantity: int = 1,
        product_id: int | None = None,
    ) -> ShoppingListItem:
        """Add an item to the in-memory shopping list."""
        item = ShoppingListItem(
            id=f"mock-item-{len(self._items) + 1}",
            description=description,
            quantity=quantity,
            product_id=product_id,
        )
        self._items.append(item)
        return item.model_copy(deep=True)

    async def remove_item(self, item_id: str) -> None:
        """Remove an item from the in-memory shopping list."""
        self._items = [item for item in self._items if item.id != item_id]

    async def clear(self) -> None:
        """Clear the in-memory shopping list."""
        self._items.clear()


class MockAHClient:
    """Drop-in async mock client for local development and tests."""

    def __init__(
        self,
        *,
        products: list[Product] | None = None,
        receipts: list[Receipt] | None = None,
    ) -> None:
        """Initialize the mock APIs with optional custom fixture data."""
        product_fixtures = deepcopy(products) if products is not None else _default_products()
        receipt_fixtures = deepcopy(receipts) if receipts is not None else _default_receipts()
        self.products = MockProductsAPI(product_fixtures)
        self.receipts = MockReceiptsAPI(receipt_fixtures)
        self.lists = MockListsAPI()

    async def __aenter__(self) -> MockAHClient:
        """Return the mock client in async context-manager usage."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Allow use in async context-manager blocks."""

    async def aclose(self) -> None:
        """Match the real client interface without external cleanup."""

    async def login(self) -> None:
        """Match the real client interface without external auth."""
