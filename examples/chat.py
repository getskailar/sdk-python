"""Example: a buffered (non-streamed) chat completion.

Run:
    SKAILAR_API_KEY=skl_live_... \\
    SKAILAR_BASE_URL=http://localhost:8080 \\
    SKAILAR_MODEL=claude-sonnet-4-6 \\
    uv run examples/chat.py
"""

from __future__ import annotations

import os

from skailar import Skailar


def main() -> None:
    with Skailar(base_url=os.environ.get("SKAILAR_BASE_URL", "https://api.skailar.com")) as client:
        completion = client.chat.completions.create(
            model=os.environ.get("SKAILAR_MODEL", "claude-sonnet-4-6"),
            messages=[{"role": "user", "content": "Hello! Say hi in one sentence."}],
            max_tokens=100,
        )
        print(completion.choices[0].message.content)


if __name__ == "__main__":
    main()
