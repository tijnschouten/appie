from __future__ import annotations

from unittest.mock import Mock

import appie


def test_login_cli_uses_asyncio_run(monkeypatch):
    def fake_run(coro):
        coro.close()

    run = Mock(side_effect=fake_run)
    monkeypatch.setattr(appie.asyncio, "run", run)

    appie.login_cli()

    run.assert_called_once()


def test_public_mock_exports():
    assert appie.MockAHClient is not None
    assert appie.AppieMockCall is not None
    assert appie.AppieMockController is not None
    assert appie.AppieMockScenario is not None
