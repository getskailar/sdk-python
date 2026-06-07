"""Resource namespaces hung off the Skailar clients."""

from __future__ import annotations

from .audio import AsyncAudioResource, AsyncSpeechStream, AudioResource, SpeechStream
from .chat import AsyncChatResource, ChatResource
from .images import AsyncImagesResource, ImagesResource
from .models import AsyncModelsResource, ModelsResource
from .uploads import AsyncUploadsResource, UploadsResource

__all__ = [
    "AudioResource",
    "AsyncAudioResource",
    "SpeechStream",
    "AsyncSpeechStream",
    "ChatResource",
    "AsyncChatResource",
    "ImagesResource",
    "AsyncImagesResource",
    "ModelsResource",
    "AsyncModelsResource",
    "UploadsResource",
    "AsyncUploadsResource",
]
