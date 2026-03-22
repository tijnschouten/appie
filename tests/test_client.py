from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
import respx
from httpx import Response

from appie.auth import BASE_URL, DEFAULT_CLIENT_ID, DEFAULT_CLIENT_VERSION, DEFAULT_USER_AGENT
from appie.client import AHClient


@pytest.mark.asyncio
@respx.mock
async def test_request_includes_auth_and_default_headers(ah_client):
    route = respx.get(f"{BASE_URL}/mobile-services/product/search/v2").mock(
        return_value=Response(200, json={"products": []})
    )

    await ah_client.products.search("melk")

    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer access-token"
    assert request.headers["User-Agent"] == DEFAULT_USER_AGENT
    assert request.headers["x-client-name"] == DEFAULT_CLIENT_ID
    assert request.headers["x-client-version"] == DEFAULT_CLIENT_VERSION
    assert request.headers["x-application"] == "AHWEBSHOP"
    assert request.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
@respx.mock
async def test_graphql_posts_to_expected_endpoint(ah_client):
    route = respx.post(f"{BASE_URL}/graphql").mock(
        return_value=Response(200, json={"data": {"posReceiptsPage": {"posReceipts": []}}})
    )

    data = await ah_client.graphql(
        (
            "query Example { posReceiptsPage(pagination: {offset: 0, limit: 1}) "
            "{ posReceipts { id } } }"
        ),
        {"limit": 1},
    )

    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer access-token"
    assert json.loads(request.content) == {
        "query": (
            "query Example { posReceiptsPage(pagination: {offset: 0, limit: 1}) "
            "{ posReceipts { id } } }"
        ),
        "variables": {"limit": 1},
    }
    assert data == {"posReceiptsPage": {"posReceipts": []}}


def test_sub_clients_share_authenticated_client(ah_client):
    assert ah_client.receipts._client is ah_client
    assert ah_client.products._client is ah_client
    assert ah_client.lists._client is ah_client


def test_extract_code_accepts_full_redirect_url(ah_client):
    code = ah_client._extract_code("appie://login-exit?code=abc123")

    assert code == "abc123"


def test_extract_code_accepts_url_with_extra_params(ah_client):
    code = ah_client._extract_code("appie://login-exit?code=abc123&state=xyz")

    assert code == "abc123"


def test_extract_code_accepts_raw_code(ah_client):
    code = ah_client._extract_code("abc123")

    assert code == "abc123"


def test_extract_code_from_redirect_target_requires_appie_scheme(ah_client):
    code = ah_client._extract_code_from_redirect_target(
        "https://example.test/callback?code=wrong-code"
    )

    assert code is None


def test_extract_code_from_redirect_target_accepts_appie_redirect(ah_client):
    code = ah_client._extract_code_from_redirect_target("appie://login-exit?code=abc123")

    assert code == "abc123"


@pytest.mark.asyncio
@respx.mock
async def test_receipt_mapping(ah_client):
    def graphql_response(request):
        payload = json.loads(request.content)
        if "FetchPosReceipts" in payload["query"]:
            return Response(
                200,
                json={
                    "data": {
                        "posReceiptsPage": {
                            "posReceipts": [
                                {
                                    "id": "receipt-1",
                                    "dateTime": "2024-04-15T10:30:00",
                                    "totalAmount": {"amount": 5.5},
                                }
                            ]
                        }
                    }
                },
            )
        return Response(
            200,
            json={
                "data": {
                    "posReceiptDetails": {
                        "id": "receipt-1",
                        "products": [
                            {
                                "id": 123,
                                "quantity": 2,
                                "name": "Halfvolle melk",
                                "price": {"amount": 1.5},
                                "amount": {"amount": 3.0},
                            }
                        ],
                    }
                }
            },
        )

    respx.post(f"{BASE_URL}/graphql").mock(side_effect=graphql_response)

    receipt = await ah_client.receipts.get_pos_receipt("receipt-1")

    assert receipt.id == "receipt-1"
    assert receipt.total == 5.5
    assert receipt.products[0].id == 123
    assert receipt.products[0].name == "Halfvolle melk"


@pytest.mark.asyncio
@respx.mock
async def test_product_search_mapping(ah_client):
    respx.get(f"{BASE_URL}/mobile-services/product/search/v2").mock(
        return_value=Response(
            200,
            json={
                "products": [
                    {
                        "webshopId": 123,
                        "title": "Halfvolle melk",
                        "brand": "AH",
                        "currentPrice": 1.99,
                        "priceBeforeBonus": 2.49,
                        "isBonus": True,
                        "bonusMechanism": "2e halve prijs",
                        "bonusStartDate": "2026-03-16",
                        "bonusEndDate": "2026-03-22",
                        "salesUnitSize": "1 l",
                        "propertyIcons": ["np_biologisch"],
                        "images": [{"url": "https://example.test/melk.jpg"}],
                    }
                ]
            },
        )
    )

    products = await ah_client.products.search("melk")

    assert len(products) == 1
    assert products[0].title == "Halfvolle melk"
    assert products[0].price == 1.99
    assert products[0].original_price == 2.49
    assert products[0].is_bonus is True
    assert products[0].bonus_label == "2e halve prijs"
    assert products[0].bonus_start_date is not None
    assert products[0].bonus_end_date is not None
    assert products[0].is_organic is True
    assert products[0].property_labels == ["np_biologisch"]


@pytest.mark.asyncio
@respx.mock
async def test_product_detail_mapping(ah_client):
    respx.get(f"{BASE_URL}/mobile-services/product/detail/v4/fir/123").mock(
        return_value=Response(
            200,
            json={
                "productId": 123,
                "productCard": {
                    "webshopId": 123,
                    "title": "Halfvolle melk",
                    "brand": "AH",
                    "currentPrice": 1.99,
                    "isBonusPrice": False,
                    "salesUnitSize": "1 l",
                    "properties": [{"label": "Biologisch"}],
                    "images": [{"url": "https://example.test/melk.jpg"}],
                },
            },
        )
    )

    product = await ah_client.products.get(123)

    assert product.id == 123
    assert product.title == "Halfvolle melk"
    assert product.is_bonus is False
    assert product.is_organic is True
    assert product.original_price is None
    assert product.property_labels == ["Biologisch"]


def test_product_mapping_requires_identifier(ah_client):
    with pytest.raises(KeyError, match="id or webshopId"):
        ah_client.products._map_product({"title": "Broken"})


def test_product_mapping_prefers_first_image_dict(ah_client):
    product = ah_client.products._map_product(
        {
            "webshopId": 123,
            "title": "Halfvolle melk",
            "currentPrice": {"amount": 1.99},
            "images": [{"url": "https://example.test/image.jpg"}],
        }
    )

    assert product.image_url == "https://example.test/image.jpg"


def test_product_mapping_uses_discount_description_when_bonus_mechanism_missing(ah_client):
    product = ah_client.products._map_product(
        {
            "webshopId": 123,
            "title": "Halfvolle melk",
            "currentPrice": 1.99,
            "extraDescriptions": ["Alleen online", "10% korting op deze Keuze Deal."],
            "labels": [{"id": "np_biologisch"}],
        }
    )

    assert product.bonus_label == "10% korting op deze Keuze Deal."
    assert product.is_bonus is None
    assert product.is_organic is True
    assert product.property_labels == ["np_biologisch"]


def test_product_mapping_hides_original_price_when_not_discounted(ah_client):
    product = ah_client.products._map_product(
        {
            "webshopId": 123,
            "title": "Halfvolle melk",
            "currentPrice": 1.99,
            "priceBeforeBonus": 1.99,
        }
    )

    assert product.original_price is None


@pytest.mark.asyncio
@respx.mock
async def test_add_shopping_list_item_mapping(ah_client):
    route = respx.patch(f"{BASE_URL}/mobile-services/shoppinglist/v2/items").mock(
        return_value=Response(
            200,
            json={
                "id": "list-1",
                "items": [
                    {
                        "listItemId": 0,
                        "description": "Halfvolle melk",
                        "quantity": 2,
                        "type": "SHOPPABLE",
                        "originCode": "TXT",
                        "vagueTermDetails": {"searchTermValue": "Halfvolle melk"},
                    }
                ],
            },
        )
    )

    item = await ah_client.lists.add_item("Halfvolle melk", quantity=2)

    assert json.loads(route.calls[0].request.content) == {
        "items": [
            {
                "description": "Halfvolle melk",
                "quantity": 2,
                "type": "SHOPPABLE",
                "originCode": "TXT",
            }
        ]
    }
    assert item.id == "txt:Halfvolle%20melk"
    assert item.description == "Halfvolle melk"
    assert item.quantity == 2
    assert item.product_id is None


@pytest.mark.asyncio
@respx.mock
async def test_add_product_shopping_list_item_uses_rest_patch_shape(ah_client):
    route = respx.patch(f"{BASE_URL}/mobile-services/shoppinglist/v2/items").mock(
        return_value=Response(
            200,
            json={
                "id": "list-1",
                "items": [
                    {
                        "listItemId": 0,
                        "quantity": 2,
                        "type": "SHOPPABLE",
                        "originCode": "PRD",
                        "productDetails": {
                            "product": {
                                "webshopId": 123,
                                "title": "Halfvolle melk",
                            }
                        },
                    }
                ],
            },
        )
    )

    item = await ah_client.lists.add_item("Halfvolle melk", quantity=2, product_id=123)

    assert json.loads(route.calls[0].request.content) == {
        "items": [
            {
                "productId": 123,
                "quantity": 2,
                "type": "SHOPPABLE",
                "originCode": "PRD",
                "description": "Halfvolle melk",
                "searchTerm": "Halfvolle melk",
            }
        ]
    }
    assert item.id == "prd:123:Halfvolle%20melk"
    assert item.description == "Halfvolle melk"
    assert item.quantity == 2
    assert item.product_id == 123


@pytest.mark.asyncio
@respx.mock
async def test_get_list_mapping(ah_client):
    respx.get(f"{BASE_URL}/mobile-services/shoppinglist/v2/items").mock(
        return_value=Response(
            200,
            json={
                "id": "list-1",
                "items": [
                    {
                        "listItemId": 11,
                        "quantity": 2,
                        "description": "Stroopwafel",
                        "vagueTermDetails": {"searchTermValue": "Stroopwafel"},
                    },
                    {
                        "listItemId": 12,
                        "quantity": 1,
                        "productDetails": {
                            "product": {
                                "webshopId": 123,
                                "title": "Halfvolle melk",
                            }
                        },
                    },
                ],
            },
        )
    )

    items = await ah_client.lists.get_list()

    assert items[0].description == "Stroopwafel"
    assert items[0].quantity == 2
    assert items[0].product_id is None
    assert items[0].id == "txt:Stroopwafel"
    assert items[1].description == "Halfvolle melk"
    assert items[1].product_id == 123
    assert items[1].id == "prd:123:Halfvolle%20melk"


@pytest.mark.asyncio
@respx.mock
async def test_get_list_returns_empty_for_missing_default_list(ah_client):
    respx.get(f"{BASE_URL}/mobile-services/shoppinglist/v2/items").mock(
        return_value=Response(200, json={"id": "list-1", "items": []})
    )

    items = await ah_client.lists.get_list()

    assert items == []


@pytest.mark.asyncio
@respx.mock
async def test_remove_text_item_uses_confirmed_patch_shape(ah_client):
    route = respx.patch(f"{BASE_URL}/mobile-services/shoppinglist/v2/items").mock(
        return_value=Response(200, json={})
    )

    await ah_client.lists.remove_item("txt:Stroopwafel")

    payload = json.loads(route.calls[0].request.content)
    assert payload == {
        "items": [
            {
                "description": "Stroopwafel",
                "quantity": 0,
                "type": "SHOPPABLE",
                "originCode": "TXT",
            }
        ]
    }


@pytest.mark.asyncio
@respx.mock
async def test_clear_removes_all_items_from_current_list(ah_client):
    get_route = respx.get(f"{BASE_URL}/mobile-services/shoppinglist/v2/items")
    get_route.mock(
        side_effect=[
            Response(
                200,
                json={
                    "id": "list-1",
                    "items": [
                        {
                            "listItemId": 11,
                            "quantity": 1,
                            "description": "Stroopwafel",
                        },
                        {
                            "listItemId": 12,
                            "quantity": 1,
                            "productDetails": {
                                "product": {
                                    "webshopId": 123,
                                    "title": "Halfvolle melk",
                                }
                            },
                        },
                    ],
                },
            )
        ]
    )
    patch_route = respx.patch(f"{BASE_URL}/mobile-services/shoppinglist/v2/items").mock(
        return_value=Response(200, json={})
    )

    await ah_client.lists.clear()

    payloads = [json.loads(call.request.content) for call in patch_route.calls]
    assert payloads == [
        {
            "items": [
                {
                    "description": "Stroopwafel",
                    "quantity": 0,
                    "type": "SHOPPABLE",
                    "originCode": "TXT",
                }
            ]
        },
        {
            "items": [
                {
                    "productId": 123,
                    "quantity": 0,
                    "type": "SHOPPABLE",
                    "originCode": "PRD",
                    "description": "Halfvolle melk",
                    "searchTerm": "Halfvolle melk",
                }
            ]
        },
    ]


@pytest.mark.asyncio
@respx.mock
async def test_remove_product_item_uses_confirmed_patch_shape(ah_client):
    route = respx.patch(f"{BASE_URL}/mobile-services/shoppinglist/v2/items").mock(
        return_value=Response(200, json={})
    )

    await ah_client.lists.remove_item("prd:104395:AH%20Zaanlander%20Belegen%2048%2B%20plakken")

    payload = json.loads(route.calls[0].request.content)
    assert payload == {
        "items": [
            {
                "productId": 104395,
                "quantity": 0,
                "type": "SHOPPABLE",
                "originCode": "PRD",
                "description": "AH Zaanlander Belegen 48+ plakken",
                "searchTerm": "AH Zaanlander Belegen 48+ plakken",
            }
        ]
    }


@pytest.mark.asyncio
async def test_client_context_manager_closes_owned_http_client():
    client = AHClient()

    async with client as entered:
        assert entered is client


@pytest.mark.asyncio
async def test_login_uses_capture_and_auth_exchange():
    client = AHClient()
    client.capture_login_code = AsyncMock(return_value="captured-code")  # type: ignore[method-assign]
    client.auth.login_with_code = AsyncMock()  # type: ignore[method-assign]

    await client.login()

    client.capture_login_code.assert_awaited_once()
    client.auth.login_with_code.assert_awaited_once_with("captured-code")
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_request_can_skip_auth(ah_client):
    route = respx.get(f"{BASE_URL}/mobile-services/product/search/v2").mock(
        return_value=Response(200, json={"products": []})
    )

    await ah_client.request(
        "GET",
        "/mobile-services/product/search/v2",
        auth_required=False,
    )

    assert "Authorization" not in route.calls[0].request.headers


@pytest.mark.asyncio
@respx.mock
async def test_graphql_raises_for_error_payload(ah_client):
    respx.post(f"{BASE_URL}/graphql").mock(
        return_value=Response(200, json={"errors": [{"message": "bad query"}]})
    )

    with pytest.raises(RuntimeError, match="GraphQL request failed"):
        await ah_client.graphql("query Broken { nope }")


def test_extract_code_raises_for_missing_code(ah_client):
    with pytest.raises(ValueError, match="authorization code"):
        ah_client._extract_code("https://example.test/nope")


@pytest.mark.asyncio
@respx.mock
async def test_receipts_return_none_when_summary_missing(ah_client):
    def graphql_response(request):
        payload = json.loads(request.content)
        if "FetchPosReceipts" in payload["query"]:
            return Response(200, json={"data": {"posReceiptsPage": {"posReceipts": []}}})
        return Response(
            200,
            json={
                "data": {
                    "posReceiptDetails": {
                        "id": "receipt-missing",
                        "products": [
                            {
                                "id": 123,
                                "quantity": 1,
                                "name": "Halfvolle melk",
                                "price": {"amount": 1.5},
                                "amount": {"amount": 1.5},
                            }
                        ],
                    }
                }
            },
        )

    respx.post(f"{BASE_URL}/graphql").mock(side_effect=graphql_response)

    receipt = await ah_client.receipts.get_pos_receipt("receipt-missing")

    assert receipt.total == 1.5
    assert receipt.products[0].name == "Halfvolle melk"
