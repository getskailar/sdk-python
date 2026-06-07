"""Tests for buffered chat completions, models, images, uploads, audio and ping."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from skailar import AsyncSkailar, Skailar
from tests.conftest import API_KEY, BASE_URL, chat_completion_payload


def test_chat_completion_sync(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=chat_completion_payload("Hi!"))
    res = client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "Hello"}],
    )
    assert res.choices[0].message.content == "Hi!"
    assert res.usage is not None
    assert res.usage.total_tokens == 3


async def test_chat_completion_async(async_client: AsyncSkailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=chat_completion_payload("Async hi!"))
    res = await async_client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "Hello"}],
    )
    assert res.choices[0].message.content == "Async hi!"


def test_authorization_header_sent(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=chat_completion_payload())
    client.chat.completions.create(
        model="claude-sonnet-4-6", messages=[{"role": "user", "content": "x"}]
    )
    request = httpx_mock.get_requests()[0]
    assert request.headers["authorization"] == f"Bearer {API_KEY}"


def test_not_given_fields_stripped(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=chat_completion_payload())
    client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "x"}],
        temperature=0.5,
    )
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["temperature"] == 0.5
    assert "top_p" not in body
    assert "max_tokens" not in body


def test_default_headers_merged_but_auth_protected(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=chat_completion_payload())
    with Skailar(
        api_key=API_KEY,
        base_url=BASE_URL,
        default_headers={"X-Client": "test", "Authorization": "Bearer attacker"},
    ) as client:
        client.chat.completions.create(
            model="claude-sonnet-4-6", messages=[{"role": "user", "content": "x"}]
        )
    request = httpx_mock.get_requests()[0]
    assert request.headers["x-client"] == "test"
    assert request.headers["authorization"] == f"Bearer {API_KEY}"


def test_per_call_headers_cannot_override_auth(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=chat_completion_payload())
    client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "x"}],
        headers={"authorization": "Bearer nope", "X-Trace": "1"},
    )
    request = httpx_mock.get_requests()[0]
    assert request.headers["authorization"] == f"Bearer {API_KEY}"
    assert request.headers["x-trace"] == "1"


def test_ping_sync(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"status": "ok", "user_id": "user-123"})
    res = client.ping()
    assert res.status == "ok"
    assert res.user_id == "user-123"


async def test_ping_async(async_client: AsyncSkailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"status": "ok", "user_id": "user-123"})
    res = await async_client.ping()
    assert res.user_id == "user-123"


def test_models_list_unwraps_envelope(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        json={
            "object": "list",
            "data": [
                {
                    "id": "claude-sonnet-4-6",
                    "object": "model",
                    "created": 1,
                    "owned_by": "anthropic",
                    "display_name": "Claude Sonnet",
                    "context_window": 200000,
                    "max_output_tokens": 8192,
                    "capabilities": {
                        "streaming": True,
                        "tool_calls": True,
                        "vision": True,
                        "json_mode": True,
                    },
                    "pricing": {
                        "input_per_mtok": 3.0,
                        "output_per_mtok": 15.0,
                        "currency": "USD",
                    },
                    "status": "active",
                }
            ],
        }
    )
    models = client.models.list()
    assert len(models) == 1
    assert models[0].id == "claude-sonnet-4-6"
    assert models[0].capabilities.vision is True


def test_models_retrieve_encodes_slash(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        json={
            "id": "google/gemini-2.5-pro",
            "object": "model",
            "created": 1,
            "owned_by": "google",
            "display_name": "Gemini 2.5 Pro",
            "context_window": 1000000,
            "max_output_tokens": 8192,
            "capabilities": {
                "streaming": True,
                "tool_calls": True,
                "vision": True,
                "json_mode": True,
            },
            "pricing": {"input_per_mtok": 1.0, "output_per_mtok": 2.0, "currency": "USD"},
            "status": "active",
            "aliases": ["gemini-pro"],
        }
    )
    model = client.models.retrieve("google/gemini-2.5-pro")
    assert model.id == "google/gemini-2.5-pro"
    assert model.aliases == ("gemini-pro",)
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/v1/models/google/gemini-2.5-pro"


def test_image_generation(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        json={"created": 1, "data": [{"url": "https://cdn/img.png", "revised_prompt": "a cat"}]}
    )
    res = client.images.generate(model="gpt-image-1", prompt="a cat")
    assert res.data[0].url == "https://cdn/img.png"


def test_upload_image_encodes_base64(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"url": "/assets/x.png", "content_type": "image/png"})
    res = client.uploads.images.create(data=b"\x89PNG", content_type="image/png")
    assert res.url == "/assets/x.png"
    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["content_type"] == "image/png"
    assert body["base64"]  # non-empty


def test_transcription(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"text": "hello world"})
    res = client.audio.transcriptions.create(file=b"RIFF....", mime="audio/wav")
    assert res.text == "hello world"


def test_speech_returns_audio_bytes(client: Skailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        content=b"ID3audio-bytes", headers={"content-type": "audio/mpeg"}
    )
    with client.audio.speech.create(input="ciao", voice="nova") as audio:
        data = audio.read()
    assert data == b"ID3audio-bytes"


async def test_speech_async_iter(async_client: AsyncSkailar, httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(content=b"mp3chunk", headers={"content-type": "audio/mpeg"})
    chunks = bytearray()
    async with await async_client.audio.speech.create(input="ciao") as audio:
        async for chunk in audio:
            chunks.extend(chunk)
    assert bytes(chunks) == b"mp3chunk"


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SKAILAR_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Missing Skailar API key"):
        Skailar(base_url=BASE_URL)
