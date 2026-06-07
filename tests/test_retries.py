"""Tests for retry behaviour: rate limits, 5xx, connection errors, side effects."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

import skailar._client as client_module
import skailar._utils as utils_module
from skailar import AsyncSkailar, Skailar, SkailarConnectionError, SkailarRateLimitError
from tests.conftest import API_KEY, BASE_URL, chat_completion_payload


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make retries instant by zeroing every delay the client may wait."""
    monkeypatch.setattr(client_module.time, "sleep", lambda _seconds: None)

    async def _async_noop(_seconds: float) -> None:
        return None

    monkeypatch.setattr(client_module.asyncio, "sleep", _async_noop)
    monkeypatch.setattr(utils_module, "backoff_delay", lambda _attempt: 0.0)
    monkeypatch.setattr(client_module, "backoff_delay", lambda _attempt: 0.0)


def _create(client: Skailar) -> str:
    res = client.chat.completions.create(
        model="claude-sonnet-4-6", messages=[{"role": "user", "content": "x"}]
    )
    return res.choices[0].message.content or ""


def test_429_then_success_is_retried(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=429, headers={"retry-after": "1"})
    httpx_mock.add_response(json=chat_completion_payload("recovered"))
    assert _create(client) == "recovered"
    assert len(httpx_mock.get_requests()) == 2


def test_retry_after_capped_at_60s(
    httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[float] = []
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: captured.append(seconds))
    httpx_mock.add_response(status_code=429, headers={"retry-after": "300"})
    httpx_mock.add_response(json=chat_completion_payload("ok"))
    with Skailar(api_key=API_KEY, base_url=BASE_URL, max_retries=2) as client:
        assert _create(client) == "ok"
    assert captured == [60.0]


def test_cap_retry_delay_helper() -> None:
    assert utils_module.cap_retry_delay(300) == 60.0
    assert utils_module.cap_retry_delay(5) == 5.0
    assert utils_module.cap_retry_delay(None) is None


def test_rate_limit_error_exposes_retry_after_seconds(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=429, headers={"retry-after": "42"})
    with Skailar(api_key=API_KEY, base_url=BASE_URL, max_retries=0) as client:
        with pytest.raises(SkailarRateLimitError) as exc:
            _create(client)
    assert exc.value.retry_after == 42


def test_5xx_retried_for_idempotent_get(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=503, json={"error": "upstream_error"})
    httpx_mock.add_response(json={"status": "ok", "user_id": "u1"})
    res = client.ping()
    assert res.user_id == "u1"
    assert len(httpx_mock.get_requests()) == 2


def test_5xx_not_retried_for_side_effect_post(client: Skailar, httpx_mock: HTTPXMock) -> None:
    from skailar import SkailarUpstreamError

    httpx_mock.add_response(status_code=502, json={"error": "upstream_error"})
    with pytest.raises(SkailarUpstreamError):
        client.images.generate(model="gpt-image-1", prompt="a cat")
    assert len(httpx_mock.get_requests()) == 1


def test_chat_completion_5xx_retried(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=500, json={"error": "upstream_error"})
    httpx_mock.add_response(json=chat_completion_payload("after retry"))
    assert _create(client) == "after retry"
    assert len(httpx_mock.get_requests()) == 2


def test_connection_error_retried_for_get(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError("boom"))
    httpx_mock.add_response(json={"status": "ok", "user_id": "u2"})
    res = client.ping()
    assert res.user_id == "u2"


def test_connection_error_not_retried_for_post(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError("boom"))
    with pytest.raises(SkailarConnectionError):
        client.images.generate(model="gpt-image-1", prompt="x")
    assert len(httpx_mock.get_requests()) == 1


def test_timeout_message_distinguished(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ReadTimeout("slow"))
    with pytest.raises(SkailarConnectionError) as exc:
        client.images.generate(model="gpt-image-1", prompt="x")
    assert "timed out" in str(exc.value).lower()
    assert exc.value.__cause__ is not None


def test_network_failure_message(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError("dns"))
    with pytest.raises(SkailarConnectionError) as exc:
        client.images.generate(model="gpt-image-1", prompt="x")
    assert "network" in str(exc.value).lower()


async def test_async_5xx_retried(async_client: AsyncSkailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=503, json={"error": "upstream_error"})
    httpx_mock.add_response(json=chat_completion_payload("async recovered"))
    res = await async_client.chat.completions.create(
        model="claude-sonnet-4-6", messages=[{"role": "user", "content": "x"}]
    )
    assert res.choices[0].message.content == "async recovered"


def test_max_retries_exhausted(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=429)
    with Skailar(api_key=API_KEY, base_url=BASE_URL, max_retries=2) as client:
        with pytest.raises(SkailarRateLimitError):
            _create(client)
    assert len(httpx_mock.get_requests()) == 3
