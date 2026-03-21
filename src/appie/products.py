"""Product search and lookup operations."""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from appie.models import Product


class RequestingClient(Protocol):
    """Protocol for clients that can make authenticated HTTP requests."""

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Send an HTTP request."""
        ...


class ProductsAPI:
    """High-level product operations."""

    def __init__(self, client: RequestingClient) -> None:
        self._client = client

    async def search(self, query: str, limit: int = 10) -> list[Product]:
        """Search products by free-text query."""
        response = await self._client.request(
            "GET",
            "/mobile-services/product/search/v2",
            params={"query": query, "sortOn": "RELEVANCE", "size": limit, "page": 0},
        )
        payload = response.json()
        products = payload.get("products") or payload.get("data") or []
        return [self._map_product(item) for item in products]

    async def get(self, product_id: int) -> Product:
        """Fetch a single product by its webshop identifier."""
        response = await self._client.request(
            "GET",
            f"/mobile-services/product/detail/v4/fir/{product_id}",
        )
        payload = response.json()
        product_card = payload.get("productCard")
        if not isinstance(product_card, dict):
            raise LookupError(f"Product {product_id} detail payload did not contain productCard.")
        return self._map_product(product_card)

    @staticmethod
    def _map_product(payload: dict) -> Product:
        return Product(
            id=int(ProductsAPI._extract_product_id(payload)),
            title=ProductsAPI._extract_title(payload),
            brand=payload.get("brand"),
            price=ProductsAPI._extract_price(payload),
            unit_size=ProductsAPI._extract_unit_size(payload),
            image_url=ProductsAPI._extract_image_url(payload),
        )

    @staticmethod
    def _extract_product_id(payload: dict) -> int:
        product_id = payload.get("id", payload.get("webshopId"))
        if product_id is None:
            raise KeyError("Product payload did not contain id or webshopId")
        return int(product_id)

    @staticmethod
    def _extract_title(payload: dict) -> str:
        title = payload.get("title") or payload.get("description")
        if not title:
            raise KeyError("Product payload did not contain title or description")
        return title

    @staticmethod
    def _extract_price(payload: dict) -> float | None:
        price = (
            payload.get("currentPrice") or payload.get("priceBeforeBonus") or payload.get("price")
        )
        if isinstance(price, dict):
            price = price.get("amount")
        return float(price) if price is not None else None

    @staticmethod
    def _extract_unit_size(payload: dict) -> str | None:
        return (
            payload.get("unitSize")
            or payload.get("salesUnitSize")
            or payload.get("unitPriceDescription")
        )

    @staticmethod
    def _extract_image_url(payload: dict) -> str | None:
        image_url = payload.get("imageUrl")
        images = payload.get("images")
        if image_url is None and isinstance(images, list) and images:
            first_image = images[0]
            if isinstance(first_image, dict):
                image_url = first_image.get("url")
        return image_url
