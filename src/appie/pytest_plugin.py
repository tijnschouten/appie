"""Pytest fixtures for downstream packages using the appie mock client."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from appie.mock import AppieMockController, MockAHClient


def build_appie_mock() -> MockAHClient:
    """Create a fresh mock client for one test."""
    return MockAHClient()


def build_appie_mock_controller(appie_mock: MockAHClient) -> AppieMockController:
    """Return the controller for a mock client."""
    return appie_mock.mock


def build_appie_mock_factory() -> Callable[..., MockAHClient]:
    """Return a factory for creating custom mock clients."""
    return MockAHClient


@pytest.fixture
def appie_mock() -> MockAHClient:
    """Return a fresh mock client for one test."""
    return build_appie_mock()


@pytest.fixture
def appie_mock_controller(appie_mock: MockAHClient) -> AppieMockController:
    """Return the controller that captures and scripts mock-client behavior."""
    return build_appie_mock_controller(appie_mock)


@pytest.fixture
def appie_mock_factory() -> Callable[..., MockAHClient]:
    """Return a factory for creating custom mock-client instances."""
    return build_appie_mock_factory()
