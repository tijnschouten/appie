"""Authentication helpers for the Albert Heijn API client."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from appie.models import StoredToken, TokenResponse

BASE_URL = "https://api.ah.nl"
DEFAULT_CLIENT_ID = "appie-ios"
DEFAULT_CLIENT_VERSION = "9.28"
DEFAULT_USER_AGENT = "Appie/9.28 (iPhone17,3; iPhone; CPU OS 26_1 like Mac OS X)"
DEFAULT_TOKEN_PATH = Path.home() / ".config" / "appie" / "tokens.json"
REFRESH_SKEW_SECONDS = 60


class AHAuthClient:
    """Manage AH access tokens, refresh tokens, and token persistence."""

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        token_path: Path | None = None,
    ) -> None:
        self._client = http_client or httpx.AsyncClient(base_url=BASE_URL)
        self._owns_client = http_client is None
        self.token_path = token_path or DEFAULT_TOKEN_PATH
        self._stored_token: StoredToken | None = self.load_tokens()

    async def __aenter__(self) -> AHAuthClient:
        """Return the auth client in async context-manager usage."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Close owned resources at context-manager exit."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client when this instance owns it."""
        if self._owns_client:
            await self._client.aclose()

    @property
    def access_token(self) -> str | None:
        """Return the current access token if one is loaded."""
        if self._stored_token is None:
            return None
        return self._stored_token.access_token

    @property
    def refresh_token_value(self) -> str | None:
        """Return the current refresh token if one is loaded."""
        if self._stored_token is None:
            return None
        return self._stored_token.refresh_token

    @property
    def token(self) -> TokenResponse | None:
        """Return the current stored token as a public token model."""
        if self._stored_token is None:
            return None
        return self._stored_token.to_token_response()

    def load_tokens(self) -> StoredToken | None:
        """Load persisted tokens from disk when available."""
        if not self.token_path.exists():
            return None
        payload = json.loads(self.token_path.read_text())
        return StoredToken.model_validate(payload)

    def save_tokens(self, token: TokenResponse) -> StoredToken:
        """Persist tokens to disk and cache the stored token in memory."""
        expires_at = datetime.now(UTC) + timedelta(seconds=token.expires_in)
        stored = StoredToken.from_token_response(token, expires_at=expires_at)
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(stored.model_dump_json(indent=2))
        self._stored_token = stored
        return stored

    def token_is_expiring(self) -> bool:
        """Return whether the current access token should be refreshed soon."""
        if self._stored_token is None:
            return True
        refresh_deadline = datetime.now(UTC) + timedelta(seconds=REFRESH_SKEW_SECONDS)
        return self._stored_token.expires_at <= refresh_deadline

    async def ensure_valid_token(self) -> TokenResponse:
        """Return a usable token, refreshing it when necessary."""
        if self._stored_token is None:
            raise RuntimeError("No stored tokens found. Run login() or login_cli() first.")
        if self.token_is_expiring():
            return await self.refresh_token(self._stored_token.refresh_token)
        return self._stored_token.to_token_response()

    async def get_anonymous_token(self) -> TokenResponse:
        """Fetch an anonymous bootstrap token."""
        response = await self._post_json(
            "/mobile-auth/v1/auth/token/anonymous",
            {"clientId": DEFAULT_CLIENT_ID},
        )
        self._raise_for_status(response, "Failed to get anonymous token")
        return TokenResponse.model_validate(response.json())

    async def login_with_code(self, code: str) -> TokenResponse:
        """Exchange an authorization code for persisted user tokens."""
        response = await self._post_json(
            "/mobile-auth/v1/auth/token",
            {
                "clientId": DEFAULT_CLIENT_ID,
                "code": code,
            },
        )
        self._raise_for_status(response, "Failed to exchange authorization code")
        token = TokenResponse.model_validate(response.json())
        self.save_tokens(token)
        return token

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh a persisted token set using the refresh token."""
        response = await self._post_json(
            "/mobile-auth/v1/auth/token/refresh",
            {
                "clientId": DEFAULT_CLIENT_ID,
                "refreshToken": refresh_token,
            },
        )
        self._raise_for_status(response, "Failed to refresh token")
        token = TokenResponse.model_validate(response.json())
        self.save_tokens(token)
        return token

    async def _post_json(self, url: str, payload: dict[str, str]) -> httpx.Response:
        return await self._client.post(
            url,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "x-client-name": DEFAULT_CLIENT_ID,
                "x-client-version": DEFAULT_CLIENT_VERSION,
                "x-application": "AHWEBSHOP",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    @staticmethod
    def _raise_for_status(response: httpx.Response, context: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = response.text.strip()
            detail = f"{context}: {exc}"
            if body:
                detail = f"{detail}\nResponse body: {body}"
            raise RuntimeError(detail) from exc
