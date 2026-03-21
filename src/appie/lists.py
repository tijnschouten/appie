"""Shopping-list operations for the Albert Heijn API client."""

from __future__ import annotations

from typing import Any, Protocol
from urllib.parse import quote, unquote

from appie.models import ShoppingListItem

ADD_ITEM_MUTATION = """
mutation AddToShoppingList($input: ShoppingListItemInput!) {
  addShoppingListItem(input: $input) {
    id
    description
    quantity
    productId
  }
}
"""

GET_LIST_PATH = "/mobile-services/shoppinglist/v2/items"


class GraphQLClient(Protocol):
    """Protocol for clients that can execute GraphQL requests."""

    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict:
        """Execute a GraphQL request."""
        ...

    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Execute an HTTP request."""
        ...


class ListsAPI:
    """High-level shopping-list operations."""

    def __init__(self, client: GraphQLClient) -> None:
        self._client = client

    async def get_list(self) -> list[ShoppingListItem]:
        """Return the current default shopping list."""
        response = await self._client.request("GET", GET_LIST_PATH)
        payload = response.json()
        items = payload.get("items") or []
        return [self._map_list_item(item) for item in items]

    async def add_item(
        self,
        description: str,
        quantity: int = 1,
        product_id: int | None = None,
    ) -> ShoppingListItem:
        """Add an item to the shopping list."""
        data = await self._client.graphql(
            ADD_ITEM_MUTATION,
            {
                "input": {
                    "description": description,
                    "quantity": quantity,
                    "productId": product_id,
                }
            },
        )
        return self._map_item(data["addShoppingListItem"])

    async def remove_item(self, item_id: str) -> None:
        """Remove an item from the shopping list."""
        payload = {"items": [self._remove_payload_from_item_id(item_id)]}
        await self._client.request("PATCH", GET_LIST_PATH, json=payload)

    async def clear(self) -> None:
        """Clear the shopping list."""
        items = await self.get_list()
        for item in items:
            await self.remove_item(item.id)

    @staticmethod
    def _map_list_item(payload: dict) -> ShoppingListItem:
        product = (payload.get("productDetails") or {}).get("product") or {}
        product_id = product.get("webshopId")
        description = payload.get("description") or product.get("title")
        if not description:
            description = payload.get("vagueTermDetails", {}).get("searchTermValue")
        if not description:
            description = f"Item {payload.get('listItemId', 'unknown')}"
        return ShoppingListItem(
            id=ListsAPI._build_item_id(description, product_id),
            description=description,
            quantity=int(payload.get("quantity", 1)),
            product_id=int(product_id) if product_id is not None else None,
        )

    @staticmethod
    def _map_item(payload: dict) -> ShoppingListItem:
        return ShoppingListItem(
            id=str(payload["id"]),
            description=payload["description"],
            quantity=int(payload.get("quantity", 1)),
            product_id=payload.get("productId"),
        )

    @staticmethod
    def _build_item_id(description: str, product_id: Any) -> str:
        encoded_description = quote(description, safe="")
        if product_id is not None:
            return f"prd:{int(product_id)}:{encoded_description}"
        return f"txt:{encoded_description}"

    @staticmethod
    def _remove_payload_from_item_id(item_id: str) -> dict[str, Any]:
        if item_id.startswith("prd:"):
            _, product_id, encoded_description = item_id.split(":", 2)
            description = unquote(encoded_description)
            return {
                "productId": int(product_id),
                "quantity": 0,
                "type": "SHOPPABLE",
                "originCode": "PRD",
                "description": description,
                "searchTerm": description,
            }
        if item_id.startswith("txt:"):
            _, encoded_description = item_id.split(":", 1)
            return {
                "description": unquote(encoded_description),
                "quantity": 0,
                "type": "SHOPPABLE",
                "originCode": "TXT",
            }
        raise ValueError(f"Unsupported shopping-list item id format: {item_id}")
