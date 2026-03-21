"""Public package exports and CLI entrypoints for python-appie."""

from __future__ import annotations

import asyncio

from appie.auth import AHAuthClient
from appie.client import AHClient
from appie.mock import MockAHClient

__all__ = ["AHAuthClient", "AHClient", "MockAHClient", "login_cli"]


def login_cli() -> None:
    """Run the interactive login CLI."""
    asyncio.run(_login_cli_async())


async def _login_cli_async() -> None:  # pragma: no cover - exercised via manual browser login
    async with AHClient() as client:
        try:
            code = await client.capture_login_code()
        except RuntimeError as exc:
            print(f"Automatic login capture failed: {exc}")
            print(f"Open this URL in your browser:\n{client.authorize_url}\n")
            redirect_or_code = input("Paste the redirect URL or raw code: ").strip()
            code = client._extract_code(redirect_or_code)
        await client.auth.login_with_code(code)
        print("✓ Logged in successfully")
