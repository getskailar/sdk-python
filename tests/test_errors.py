"""Tests for the error hierarchy and HTTP status mapping."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from skailar import (
    Skailar,
    SkailarAPIError,
    SkailarAuthError,
    SkailarBadRequestError,
    SkailarError,
    SkailarNotFoundError,
    SkailarRateLimitError,
)
from tests.conftest import chat_completion_payload


def _create(client: Skailar) -> None:
    client.chat.completions.create(
        model="claude-sonnet-4-6", messages=[{"role": "user", "content": "x"}]
    )


def test_401_maps_to_auth_error(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=401, json={"error": "invalid_api_key"})
    with pytest.raises(SkailarAuthError) as exc:
        _create(client)
    assert exc.value.status == 401
    assert exc.value.code == "invalid_api_key"
    assert isinstance(exc.value, SkailarError)


def test_400_maps_to_bad_request(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        status_code=400, json={"error": {"type": "bad_request", "message": "nope"}}
    )
    with pytest.raises(SkailarBadRequestError) as exc:
        _create(client)
    assert exc.value.code == "bad_request"
    assert str(exc.value) == "nope"


def test_404_maps_to_not_found(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404, json={"error": "not_found"})
    with pytest.raises(SkailarNotFoundError):
        client.models.retrieve("does-not-exist")


def test_request_id_captured(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        status_code=401,
        json={"error": "invalid_api_key"},
        headers={"x-request-id": "req-789"},
    )
    with pytest.raises(SkailarAuthError) as exc:
        _create(client)
    assert exc.value.request_id == "req-789"


def test_raw_body_preserved_when_not_json(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=400, content=b"plain text error")
    with pytest.raises(SkailarBadRequestError) as exc:
        _create(client)
    assert exc.value.raw == "plain text error"


def test_400_not_retried(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=400, json={"error": "bad_request"})
    with pytest.raises(SkailarBadRequestError):
        _create(client)
    assert len(httpx_mock.get_requests()) == 1


def test_unmapped_status_is_plain_api_error(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=418, json={"error": "teapot"})
    with pytest.raises(SkailarAPIError) as exc:
        _create(client)
    assert exc.value.status == 418
    assert not isinstance(exc.value, SkailarRateLimitError)


def test_in_band_stream_error_raised(client: Skailar, httpx_mock: HTTPXMock) -> None:
    import httpx

    body = b'data: {"error": {"type": "upstream_error", "message": "boom"}}\n\n'
    httpx_mock.add_response(
        stream=httpx.ByteStream(body), headers={"content-type": "text/event-stream"}
    )
    with pytest.raises(SkailarAPIError) as exc:
        stream = client.chat.completions.create(
            model="claude-sonnet-4-6",
            messages=[{"role": "user", "content": "x"}],
            stream=True,
        )
        for _ in stream:
            pass
    assert exc.value.code == "upstream_error"


def test_success_after_error_status_path(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=chat_completion_payload("ok"))
    res = client.chat.completions.create(
        model="claude-sonnet-4-6", messages=[{"role": "user", "content": "x"}]
    )
    assert res.choices[0].message.content == "ok"
