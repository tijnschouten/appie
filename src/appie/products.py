"""Product search and lookup operations."""

from __future__ import annotations

from datetime import date
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
        property_labels = ProductsAPI._extract_property_labels(payload)
        return Product(
            id=int(ProductsAPI._extract_product_id(payload)),
            title=ProductsAPI._extract_title(payload),
            brand=payload.get("brand"),
            price=ProductsAPI._extract_price(payload),
            original_price=ProductsAPI._extract_original_price(payload),
            is_bonus=ProductsAPI._extract_is_bonus(payload),
            bonus_label=ProductsAPI._extract_bonus_label(payload),
            bonus_start_date=ProductsAPI._extract_date(payload.get("bonusStartDate")),
            bonus_end_date=ProductsAPI._extract_date(payload.get("bonusEndDate")),
            is_organic=ProductsAPI._extract_is_organic(payload, property_labels),
            property_labels=property_labels,
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
    def _extract_original_price(payload: dict) -> float | None:
        original_price = payload.get("priceBeforeBonus")
        if isinstance(original_price, dict):
            original_price = original_price.get("amount")
        if original_price is None:
            return None
        current_price = ProductsAPI._extract_price(payload)
        original_value = float(original_price)
        if current_price is None or original_value <= current_price:
            return None
        return original_value

    @staticmethod
    def _extract_is_bonus(payload: dict) -> bool | None:
        is_bonus = payload.get("isBonus")
        if is_bonus is not None:
            return bool(is_bonus)
        is_bonus_price = payload.get("isBonusPrice")
        if is_bonus_price is not None:
            return bool(is_bonus_price)
        if payload.get("bonusMechanism") or payload.get("bonusStartDate"):
            return True
        return None

    @staticmethod
    def _extract_bonus_label(payload: dict) -> str | None:
        label = payload.get("bonusMechanism")
        if isinstance(label, str) and label.strip():
            return label
        for description in ProductsAPI._coerce_strings(payload.get("extraDescriptions")):
            if "korting" in description.lower():
                return description
        return None

    @staticmethod
    def _extract_date(value: Any) -> date | None:
        if isinstance(value, str) and value:
            return date.fromisoformat(value)
        return None

    @staticmethod
    def _extract_property_labels(payload: dict) -> list[str]:
        labels: list[str] = []
        labels.extend(ProductsAPI._coerce_strings(payload.get("propertyIcons")))
        labels.extend(ProductsAPI._extract_property_entries(payload.get("properties")))
        labels.extend(ProductsAPI._extract_property_entries(payload.get("labels")))
        return list(dict.fromkeys(label for label in labels if label))

    @staticmethod
    def _coerce_strings(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    @staticmethod
    def _extract_property_entries(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        entries = [item for item in value if isinstance(item, str)]
        entries.extend(
            label
            for item in value
            for label in [ProductsAPI._extract_property_entry(item)]
            if label is not None
        )
        return entries

    @staticmethod
    def _extract_property_entry(item: Any) -> str | None:
        if not isinstance(item, dict):
            return None
        label = item.get("label") or item.get("name") or item.get("title") or item.get("id")
        if isinstance(label, str):
            return label
        return None

    @staticmethod
    def _extract_is_organic(payload: dict, property_labels: list[str]) -> bool | None:
        organic = payload.get("isOrganic")
        if organic is not None:
            return bool(organic)
        organic_labels = {"biologisch", "organic", "bio", "np_biologisch"}
        normalized = {label.strip().lower() for label in property_labels if label.strip()}
        if normalized & organic_labels:
            return True
        return None

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
