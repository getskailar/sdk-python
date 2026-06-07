# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.1] - 2026-06-07

Initial pre-release. Python port of the Skailar TypeScript SDK, with the same
API surface (resource paths, method naming, error shape) but Pythonic idioms
(sync/async split, context managers, `NOT_GIVEN` sentinel, frozen dataclasses).

### Added

- Synchronous `Skailar` and asynchronous `AsyncSkailar` clients, both usable as
  (async) context managers.
- Chat completions (`chat.completions.create`) with JSON and SSE streaming.
- Model discovery (`models.list`, `models.retrieve`).
- Image generation (`images.generate`).
- Audio transcription (`audio.transcriptions.create`) and speech synthesis
  (`audio.speech.create`, streaming MP3).
- Storage uploads (`uploads.images.create`, `uploads.files.create`).
- Key verification utility (`ping`).
- Typed error hierarchy (`SkailarError` and subclasses) carrying `status`,
  `code`, `request_id`, `raw` and the originating exception via `__cause__`.
- Dependency-free SSE parser tolerant of `\n`, `\r\n` and `\r` line terminators.
- Automatic retries with capped, jittered exponential backoff.
- Shipped already-corrected for the bugs fixed across the TypeScript SDK's
  `0.0.1`–`0.0.5` line:
  - retries do not leak listeners or leave pending async tasks on an external
    cancellation;
  - connection-timeout errors are distinguished from generic network failures in
    the error message;
  - early stream exit closes the underlying connection;
  - the `Authorization` header cannot be overridden by `default_headers` or
    per-call headers;
  - requests with billed side effects (image generation, speech, transcription,
    uploads) are not retried, to avoid double charges;
  - `Retry-After` delays are capped at 60 seconds.

[Unreleased]: https://github.com/getskailar/sdk-python/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/getskailar/sdk-python/releases/tag/v0.0.1
