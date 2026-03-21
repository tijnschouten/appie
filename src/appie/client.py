"""Main async client for interacting with Albert Heijn endpoints."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from appie.auth import (
    BASE_URL,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_VERSION,
    DEFAULT_USER_AGENT,
    AHAuthClient,
)


class AHClient:
    """High-level async client that exposes products, receipts, and lists APIs."""

    user_agent = DEFAULT_USER_AGENT
    graphql_url = f"{BASE_URL}/graphql"
    authorize_url = (
        "https://login.ah.nl/login"
        f"?client_id={DEFAULT_CLIENT_ID}&redirect_uri=appie://login-exit&response_type=code"
    )

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient | None = None,
        auth_client: AHAuthClient | None = None,
    ) -> None:
        default_headers = {
            "User-Agent": self.user_agent,
            "x-client-name": DEFAULT_CLIENT_ID,
            "x-client-version": DEFAULT_CLIENT_VERSION,
            "x-application": "AHWEBSHOP",
            "Content-Type": "application/json",
        }
        self._client = http_client or httpx.AsyncClient(base_url=BASE_URL, headers=default_headers)
        if http_client is not None:
            self._client.headers.update(default_headers)
        self._owns_client = http_client is None
        self.auth = auth_client or AHAuthClient(http_client=self._client)

        from appie.lists import ListsAPI
        from appie.products import ProductsAPI
        from appie.receipts import ReceiptsAPI

        self.receipts = ReceiptsAPI(self)
        self.products = ProductsAPI(self)
        self.lists = ListsAPI(self)

    async def __aenter__(self) -> AHClient:
        """Return the client in async context-manager usage."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Close owned resources at context-manager exit."""
        await self.aclose()

    async def aclose(self) -> None:
        """Close the auth and HTTP clients when owned by this instance."""
        await self.auth.aclose()
        if self._owns_client:
            await self._client.aclose()

    async def login(self) -> None:
        """Run the browser-assisted login flow and persist the resulting tokens."""
        code = await self.capture_login_code()
        await self.auth.login_with_code(code)

    async def capture_login_code(
        self,
        timeout_seconds: float = 300,
    ) -> str:  # pragma: no cover - exercised via manual browser login
        """Open a browser, capture the AH redirect code, and return it."""
        async_playwright, playwright_error = self._load_playwright()
        try:
            return await self._capture_login_code_in_browser(async_playwright, timeout_seconds)
        except playwright_error as exc:
            raise RuntimeError(
                "Automatic browser login could not start. Ensure Google Chrome is installed, "
                "or fall back to entering the raw code manually."
            ) from exc

    @staticmethod
    def _load_playwright() -> tuple[Any, type[Exception]]:  # pragma: no cover
        try:
            from playwright.async_api import Error as PlaywrightError
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install project dependencies again and ensure the "
                "Playwright browser runtime is available."
            ) from exc
        return async_playwright, PlaywrightError

    async def _capture_login_code_in_browser(
        self,
        async_playwright: Any,
        timeout_seconds: float,
    ) -> str:  # pragma: no cover - browser integration helper
        """Capture the login code from the browser redirect target."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(channel="chrome", headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            code_future: asyncio.Future[str] = asyncio.get_running_loop().create_future()
            self._register_login_capture_handlers(page, code_future)
            await page.goto(self.authorize_url, wait_until="domcontentloaded")
            print(
                "A Chrome window was opened for AH login. Complete the login there; "
                "the auth code will be captured automatically."
            )

            try:
                return await asyncio.wait_for(code_future, timeout=timeout_seconds)
            finally:
                await context.close()
                await browser.close()

    def _register_login_capture_handlers(
        self,
        page: Any,
        code_future: asyncio.Future[str],
    ) -> None:  # pragma: no cover - browser integration helper
        """Attach event handlers that resolve when the app redirect is seen."""
        page.on(
            "framenavigated",
            lambda frame: self._resolve_code_future(
                code_future,
                self._extract_code_from_redirect_target(frame.url),
            ),
        )
        page.on(
            "request",
            lambda request: self._resolve_code_future(
                code_future,
                self._extract_code_from_redirect_target(request.url),
            ),
        )
        page.on(
            "requestfailed",
            lambda request: self._resolve_code_future(
                code_future,
                self._extract_code_from_redirect_target(request.url),
            ),
        )
        page.on(
            "response",
            lambda response: asyncio.create_task(
                self._handle_login_response(response, code_future)
            ),
        )

    @staticmethod
    def _resolve_code_future(
        code_future: asyncio.Future[str],
        candidate: str | None,
    ) -> None:  # pragma: no cover - browser integration helper
        """Resolve the login-code future once a valid code is seen."""
        if candidate and not code_future.done():
            code_future.set_result(candidate)

    async def _handle_login_response(
        self,
        response: Any,
        code_future: asyncio.Future[str],
    ) -> None:  # pragma: no cover - browser integration helper
        """Inspect response headers for the redirect target."""
        try:
            headers = await response.all_headers()
        except Exception:
            return
        self._resolve_code_future(
            code_future,
            self._extract_code_from_redirect_target(headers.get("location")),
        )

    async def request(
        self,
        method: str,
        url: str,
        *,
        auth_required: bool = True,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send an HTTP request with default headers and optional bearer auth."""
        merged_headers = dict(headers or {})
        if auth_required:
            token = await self.auth.ensure_valid_token()
            merged_headers["Authorization"] = f"{token.token_type} {token.access_token}"
        response = await self._client.request(method, url, headers=merged_headers, **kwargs)
        response.raise_for_status()
        return response

    async def graphql(
        self,
        query: str,
        variables: Mapping[str, object] | None = None,
    ) -> dict:
        """Send a GraphQL request and return the `data` payload."""
        response = await self.request(
            "POST",
            self.graphql_url,
            json={"query": query, "variables": dict(variables or {})},
        )
        payload = response.json()
        if "errors" in payload:
            raise RuntimeError(f"GraphQL request failed: {payload['errors']}")
        return payload["data"]

    @staticmethod
    def _extract_code(value: str) -> str:
        """Extract an auth code from a redirect URL or raw code string."""
        code = AHClient._extract_code_from_text(value)
        if not code:
            raise ValueError("Input did not contain an authorization code.")
        return code

    @staticmethod
    def _extract_code_from_text(value: str) -> str | None:
        """Extract a code from a raw string or URL query string."""
        stripped = value.strip()
        if stripped and "://" not in stripped and "?" not in stripped and "=" not in stripped:
            return stripped
        parsed = urlparse(stripped)
        code = parse_qs(parsed.query).get("code", [None])[0]
        return code

    @staticmethod
    def _extract_code_from_redirect_target(value: str | None) -> str | None:
        """Extract a code only from the expected `appie://login-exit` redirect target."""
        if not value:
            return None
        parsed = urlparse(value.strip())
        if parsed.scheme != "appie":
            return None
        if parsed.netloc != "login-exit" and parsed.path != "/login-exit":
            return None
        return parse_qs(parsed.query).get("code", [None])[0]
