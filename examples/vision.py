"""Example: multimodal (vision) chat using an inline image content part.

Supplies an image as a ``data:`` URI built from local bytes; an HTTPS URL
returned by the uploads API works the same way. Run:
    SKAILAR_API_KEY=skl_live_... \\
    SKAILAR_BASE_URL=http://localhost:8080 \\
    SKAILAR_MODEL=gemini-2.5-flash \\
    uv run examples/vision.py
"""

from __future__ import annotations

import os

from skailar import Skailar

TINY_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def main() -> None:
    with Skailar(base_url=os.environ.get("SKAILAR_BASE_URL", "https://api.skailar.com")) as client:
        completion = client.chat.completions.create(
            model=os.environ.get("SKAILAR_MODEL", "claude-sonnet-4-6"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What color is this image, in one word?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{TINY_PNG_BASE64}",
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=50,
        )
        print(completion.choices[0].message.content)


if __name__ == "__main__":
    main()
