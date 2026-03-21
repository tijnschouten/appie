from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
import respx
from httpx import Request, Response

from appie.auth import (
    BASE_URL,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_VERSION,
    DEFAULT_USER_AGENT,
    AHAuthClient,
)
from appie.models import TokenResponse


@pytest.mark.asyncio
@respx.mock
async def test_get_anonymous_token(auth_client):
    route = respx.post(f"{BASE_URL}/mobile-auth/v1/auth/token/anonymous").mock(
        return_value=Response(
            200,
            json={
                "access_token": "anon-access",
                "refresh_token": "anon-refresh",
                "expires_in": 1800,
            },
        )
    )

    token = await auth_client.get_anonymous_token()

    assert route.called
    request = route.calls[0].request
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["User-Agent"] == DEFAULT_USER_AGENT
    assert request.headers["x-client-name"] == DEFAULT_CLIENT_ID
    assert request.headers["x-client-version"] == DEFAULT_CLIENT_VERSION
    assert request.headers["x-application"] == "AHWEBSHOP"
    assert json.loads(request.content.decode()) == {"clientId": DEFAULT_CLIENT_ID}
    assert token.access_token == "anon-access"
    assert token.refresh_token == "anon-refresh"
    assert token.token_type == "Bearer"


@pytest.mark.asyncio
@respx.mock
async def test_login_with_code_persists_tokens(auth_client):
    route = respx.post(f"{BASE_URL}/mobile-auth/v1/auth/token").mock(
        return_value=Response(
            200,
            json={
                "access_token": "user-access",
                "refresh_token": "user-refresh",
                "expires_in": 3600,
            },
        )
    )

    token = await auth_client.login_with_code("abc123")

    saved = json.loads(auth_client.token_path.read_text())
    request = route.calls[0].request
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["User-Agent"] == DEFAULT_USER_AGENT
    assert request.headers["x-client-name"] == DEFAULT_CLIENT_ID
    assert request.headers["x-client-version"] == DEFAULT_CLIENT_VERSION
    assert request.headers["x-application"] == "AHWEBSHOP"
    assert json.loads(request.content.decode()) == {
        "clientId": DEFAULT_CLIENT_ID,
        "code": "abc123",
    }
    assert token == TokenResponse(
        access_token="user-access",
        refresh_token="user-refresh",
        expires_in=3600,
        token_type="Bearer",
    )
    assert saved["access_token"] == "user-access"
    assert saved["refresh_token"] == "user-refresh"
    assert "expires_at" in saved


@pytest.mark.asyncio
@respx.mock
async def test_refresh_token_updates_stored_tokens(auth_client):
    route = respx.post(f"{BASE_URL}/mobile-auth/v1/auth/token/refresh").mock(
        return_value=Response(
            200,
            json={
                "access_token": "refreshed-access",
                "refresh_token": "refreshed-refresh",
                "expires_in": 7200,
            },
        )
    )

    token = await auth_client.refresh_token("refresh-token")

    assert route.called
    request = route.calls[0].request
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["User-Agent"] == DEFAULT_USER_AGENT
    assert request.headers["x-client-name"] == DEFAULT_CLIENT_ID
    assert request.headers["x-client-version"] == DEFAULT_CLIENT_VERSION
    assert request.headers["x-application"] == "AHWEBSHOP"
    assert json.loads(request.content.decode()) == {
        "clientId": DEFAULT_CLIENT_ID,
        "refreshToken": "refresh-token",
    }
    assert token.access_token == "refreshed-access"
    assert auth_client.access_token == "refreshed-access"


def test_load_tokens_from_disk(token_path):
    token_path.write_text(
        json.dumps(
            {
                "access_token": "stored-access",
                "refresh_token": "stored-refresh",
                "expires_in": 1200,
                "token_type": "Bearer",
                "expires_at": datetime.now(UTC).isoformat(),
            }
        )
    )

    from appie.auth import AHAuthClient

    client = AHAuthClient(token_path=token_path)
    assert client.access_token == "stored-access"


@pytest.mark.asyncio
@respx.mock
async def test_ensure_valid_token_refreshes_when_expiring(auth_client):
    auth_client.save_tokens(
        TokenResponse(
            access_token="old-access",
            refresh_token="refresh-me",
            expires_in=1,
            token_type="Bearer",
        )
    )
    auth_client._stored_token = auth_client._stored_token.model_copy(
        update={"expires_at": datetime.now(UTC) - timedelta(seconds=1)}
    )
    respx.post(f"{BASE_URL}/mobile-auth/v1/auth/token/refresh").mock(
        return_value=Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
            },
        )
    )

    token = await auth_client.ensure_valid_token()

    assert token.access_token == "new-access"
    assert auth_client.access_token == "new-access"


@pytest.mark.asyncio
async def test_auth_context_manager_closes_owned_client(token_path):
    client = AHAuthClient(token_path=token_path)
    await client.__aenter__()
    await client.__aexit__(None, None, None)

    assert client.access_token is None
    assert client.refresh_token_value is None
    assert client.token is None
    assert client.token_is_expiring() is True


def test_raise_for_status_includes_response_body():
    request = Request("POST", f"{BASE_URL}/mobile-auth/v1/auth/token")
    response = Response(400, request=request, text='{"message":"bad"}')

    with pytest.raises(RuntimeError, match="Response body:"):
        AHAuthClient._raise_for_status(response, "Auth failed")


@pytest.mark.asyncio
async def test_ensure_valid_token_returns_cached_token_without_refresh(auth_client, token_response):
    auth_client.save_tokens(token_response)

    token = await auth_client.ensure_valid_token()

    assert token.access_token == token_response.access_token


def test_load_tokens_returns_none_when_missing(token_path):
    client = AHAuthClient(token_path=token_path)
    assert client.load_tokens() is None
