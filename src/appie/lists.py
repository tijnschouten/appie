"""Shopping-list operations for the Albert Heijn API client."""

from __future__ import annotations

from typing import Any, Protocol

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


class GraphQLClient(Protocol):
    """Protocol for clients that can execute GraphQL requests."""

    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict:
        """Execute a GraphQL request."""
        ...


class ListsAPI:
    """High-level shopping-list operations."""

    def __init__(self, client: GraphQLClient) -> None:
        self._client = client

    async def get_list(self) -> list[ShoppingListItem]:
        """Return the current shopping list when the query shape is confirmed."""
        raise NotImplementedError(
            "Shopping-list query shape is not confirmed yet. "
            "The public method is reserved for a future verified GraphQL query."
        )

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
        """Remove an item from the shopping list when the mutation is confirmed."""
        raise NotImplementedError(
            f"Shopping-list remove mutation is not confirmed yet for item {item_id}."
        )

    async def clear(self) -> None:
        """Clear the shopping list when the mutation is confirmed."""
        raise NotImplementedError("Shopping-list clear mutation is not confirmed yet.")

    @staticmethod
    def _map_item(payload: dict) -> ShoppingListItem:
        return ShoppingListItem(
            id=str(payload["id"]),
            description=payload["description"],
            quantity=int(payload.get("quantity", 1)),
            product_id=payload.get("productId"),
        )
