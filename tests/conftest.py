from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from appie.auth import AHAuthClient
from appie.client import AHClient
from appie.models import TokenResponse


@pytest.fixture
def token_response() -> TokenResponse:
    return TokenResponse(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_in=3600,
        token_type="Bearer",
    )


@pytest.fixture
def token_path(tmp_path: Path) -> Path:
    return tmp_path / "tokens.json"


@pytest_asyncio.fixture
async def async_http_client():
    async with httpx.AsyncClient(base_url="https://api.ah.nl") as client:
        yield client


@pytest.fixture
def auth_client(async_http_client: httpx.AsyncClient, token_path: Path) -> AHAuthClient:
    return AHAuthClient(http_client=async_http_client, token_path=token_path)


@pytest.fixture
def ah_client(auth_client: AHAuthClient, async_http_client: httpx.AsyncClient) -> AHClient:
    auth_client.save_tokens(
        TokenResponse(
            access_token="access-token",
            refresh_token="refresh-token",
            expires_in=3600,
            token_type="Bearer",
        )
    )
    return AHClient(http_client=async_http_client, auth_client=auth_client)
