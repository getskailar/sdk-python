"""The audio resource: ``client.audio.transcriptions.create(...)`` and
``client.audio.speech.create(...)``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from types import TracebackType
from typing import TYPE_CHECKING

import httpx

from .._base_client import FinalRequestOptions
from .._types import NOT_GIVEN, Headers, NotGiven, Timeout
from .._utils import strip_not_given, to_base64
from ..types.audio import BinaryInput, SpeechVoice, TranscriptionMime, TranscriptionResponse

if TYPE_CHECKING:
    from .._client import AsyncSkailar, Skailar

__all__ = [
    "AudioResource",
    "AsyncAudioResource",
    "SpeechStream",
    "AsyncSpeechStream",
]


class SpeechStream:
    """A closeable, iterable stream of synthesized ``audio/mpeg`` bytes.

    Returned by :meth:`AudioSpeech.create`. Iterate it for byte chunks, call
    :meth:`read` to buffer the whole payload, or use it as a context manager::

        with client.audio.speech.create(input="hi", voice="nova") as audio:
            data = audio.read()
    """

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self._closed = False

    def __iter__(self) -> Iterator[bytes]:
        try:
            yield from self._response.iter_bytes()
        finally:
            self.close()

    def read(self) -> bytes:
        """Buffer and return the entire audio payload as bytes."""
        try:
            return self._response.read()
        finally:
            self.close()

    def close(self) -> None:
        """Close the underlying connection."""
        if self._closed:
            return
        self._closed = True
        self._response.close()

    def __enter__(self) -> SpeechStream:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncSpeechStream:
    """The async counterpart of :class:`SpeechStream`.

    Iterate with ``async for`` or buffer via ``await audio.read()``; use it as an
    async context manager::

        async with await client.audio.speech.create(input="hi") as audio:
            data = await audio.read()
    """

    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self._closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        try:
            async for chunk in self._response.aiter_bytes():
                yield chunk
        finally:
            await self.close()

    async def read(self) -> bytes:
        """Buffer and return the entire audio payload as bytes."""
        try:
            return await self._response.aread()
        finally:
            await self.close()

    async def close(self) -> None:
        """Close the underlying connection."""
        if self._closed:
            return
        self._closed = True
        await self._response.aclose()

    async def __aenter__(self) -> AsyncSpeechStream:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()


class AudioTranscriptions:
    """Synchronous speech-to-text operations (Whisper-backed)."""

    def __init__(self, client: Skailar) -> None:
        self._client = client

    def create(
        self,
        *,
        file: BinaryInput,
        mime: TranscriptionMime | NotGiven = NOT_GIVEN,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> TranscriptionResponse:
        """Transcribe an audio clip to text.

        The supplied bytes are base64-encoded client-side into the gateway's
        ``base64`` field.

        Args:
            file: The audio to transcribe, as ``bytes`` or a pre-encoded base64 ``str``.
            mime: MIME type of the supplied audio (default ``"audio/wav"``).
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            The :class:`TranscriptionResponse`.
        """
        body = strip_not_given({"base64": to_base64(file), "mime": mime})
        data = self._client.request(
            FinalRequestOptions(
                method="POST",
                path="/v1/audio/transcriptions",
                expect="json",
                body=body,
                idempotent=False,
                timeout=timeout,
                headers=headers,
            )
        )
        return TranscriptionResponse.from_dict(data)


class AudioSpeech:
    """Synchronous text-to-speech operations."""

    def __init__(self, client: Skailar) -> None:
        self._client = client

    def create(
        self,
        *,
        input: str,
        voice: SpeechVoice | NotGiven = NOT_GIVEN,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> SpeechStream:
        """Synthesize speech and return the raw MP3 audio stream.

        Unlike the JSON endpoints, this returns the response body stream directly
        so large audio payloads need not be buffered in memory.

        Args:
            input: Text to synthesize; limited to 4000 characters by the gateway.
            voice: Voice to speak with (default ``"nova"``).
            timeout: Optional per-call timeout override.
            headers: Optional per-call extra headers.

        Returns:
            A :class:`SpeechStream` of ``audio/mpeg`` bytes.

        Raises:
            SkailarBadRequestError: On HTTP 400 (e.g. text exceeding 4000 chars).
        """
        request_headers = {"Accept": "audio/mpeg", **(headers or {})}
        body = strip_not_given({"input": input, "voice": voice})
        response: httpx.Response = self._client.request(
            FinalRequestOptions(
                method="POST",
                path="/v1/audio/speech",
                expect="binary",
                body=body,
                idempotent=False,
                timeout=timeout,
                headers=request_headers,
            )
        )
        return SpeechStream(response)


class AudioResource:
    """The synchronous audio resource root, grouping transcription and speech."""

    def __init__(self, client: Skailar) -> None:
        self.transcriptions = AudioTranscriptions(client)
        self.speech = AudioSpeech(client)


class AsyncAudioTranscriptions:
    """Asynchronous speech-to-text operations."""

    def __init__(self, client: AsyncSkailar) -> None:
        self._client = client

    async def create(
        self,
        *,
        file: BinaryInput,
        mime: TranscriptionMime | NotGiven = NOT_GIVEN,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> TranscriptionResponse:
        """Async counterpart of :meth:`AudioTranscriptions.create`."""
        body = strip_not_given({"base64": to_base64(file), "mime": mime})
        data = await self._client.request(
            FinalRequestOptions(
                method="POST",
                path="/v1/audio/transcriptions",
                expect="json",
                body=body,
                idempotent=False,
                timeout=timeout,
                headers=headers,
            )
        )
        return TranscriptionResponse.from_dict(data)


class AsyncAudioSpeech:
    """Asynchronous text-to-speech operations."""

    def __init__(self, client: AsyncSkailar) -> None:
        self._client = client

    async def create(
        self,
        *,
        input: str,
        voice: SpeechVoice | NotGiven = NOT_GIVEN,
        timeout: Timeout | None = None,
        headers: Headers | None = None,
    ) -> AsyncSpeechStream:
        """Async counterpart of :meth:`AudioSpeech.create`."""
        request_headers = {"Accept": "audio/mpeg", **(headers or {})}
        body = strip_not_given({"input": input, "voice": voice})
        response: httpx.Response = await self._client.request(
            FinalRequestOptions(
                method="POST",
                path="/v1/audio/speech",
                expect="binary",
                body=body,
                idempotent=False,
                timeout=timeout,
                headers=request_headers,
            )
        )
        return AsyncSpeechStream(response)


class AsyncAudioResource:
    """The asynchronous audio resource root."""

    def __init__(self, client: AsyncSkailar) -> None:
        self.transcriptions = AsyncAudioTranscriptions(client)
        self.speech = AsyncAudioSpeech(client)
