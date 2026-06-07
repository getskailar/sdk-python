# Skailar SDK for Python

[![PyPI version](https://img.shields.io/pypi/v/skailar-ai.svg)](https://pypi.org/project/skailar-ai/)

The Skailar SDK for Python provides access to the [Skailar API](https://skailar.com) — an OpenAI-compatible, multi-provider LLM gateway — from Python applications.

## Installation

```sh
uv add skailar-ai
# or: pip install skailar-ai
```

The distribution is named `skailar-ai` on PyPI; the import is `skailar`.

## Getting started

```python
import os
from skailar import Skailar

client = Skailar(
    api_key=os.environ.get("SKAILAR_API_KEY"),  # This is the default and can be omitted
)

completion = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[
        {
            "role": "user",
            "content": "Hello, Skailar",
        }
    ],
)
print(completion.choices[0].message.content)
```

### Streaming

```python
with client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Count to ten."}],
    stream=True,
) as stream:
    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
```

An async client (`AsyncSkailar`) with an identical surface is also available.

## Requirements

Python 3.10+

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
