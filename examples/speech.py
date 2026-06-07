"""Example: text-to-speech, writing the synthesized MP3 to a file.

Run:
    SKAILAR_API_KEY=skl_live_... \\
    SKAILAR_BASE_URL=http://localhost:8080 \\
    uv run examples/speech.py
"""

from __future__ import annotations

import os

from skailar import Skailar


def main() -> None:
    with Skailar(base_url=os.environ.get("SKAILAR_BASE_URL", "https://api.skailar.com")) as client:
        with client.audio.speech.create(input="Ciao dal SDK di Skailar.", voice="nova") as audio:
            with open("speech.mp3", "wb") as out:
                for chunk in audio:
                    out.write(chunk)
    print("Wrote speech.mp3")


if __name__ == "__main__":
    main()
