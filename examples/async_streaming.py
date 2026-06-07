"""Example: asynchronous streaming chat completion.

Run:
    SKAILAR_API_KEY=skl_live_... \\
    SKAILAR_BASE_URL=http://localhost:8080 \\
    SKAILAR_MODEL=claude-sonnet-4-6 \\
    uv run examples/async_streaming.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from skailar import AsyncSkailar


async def main() -> None:
    async with AsyncSkailar(
        base_url=os.environ.get("SKAILAR_BASE_URL", "https://api.skailar.com")
    ) as client:
        async with await client.chat.completions.create(
            model=os.environ.get("SKAILAR_MODEL", "claude-sonnet-4-6"),
            messages=[{"role": "user", "content": "Count to 5."}],
            stream=True,
        ) as stream:
            async for chunk in stream:
                sys.stdout.write(chunk.choices[0].delta.content or "")
                sys.stdout.flush()
        print()


if __name__ == "__main__":
    asyncio.run(main())
