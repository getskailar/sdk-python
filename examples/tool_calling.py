"""Example: function/tool calling, OpenAI-compatible.

Defines one tool, lets the model decide to call it, then feeds a fabricated tool
result back for a final answer. Run:
    SKAILAR_API_KEY=skl_live_... \\
    SKAILAR_BASE_URL=http://localhost:8080 \\
    SKAILAR_MODEL=gpt-5-mini \\
    uv run examples/tool_calling.py
"""

from __future__ import annotations

import json
import os

from skailar import Skailar
from skailar.types.chat import ChatCompletionMessageParam, Tool

WEATHER_TOOL: Tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        },
    },
}


def main() -> None:
    model = os.environ.get("SKAILAR_MODEL", "claude-sonnet-4-6")
    messages: list[ChatCompletionMessageParam] = [
        {"role": "user", "content": "What's the weather in Paris? Use the tool."},
    ]

    with Skailar(base_url=os.environ.get("SKAILAR_BASE_URL", "https://api.skailar.com")) as client:
        first = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[WEATHER_TOOL],
            tool_choice="auto",
            max_tokens=200,
        )
        tool_calls = first.choices[0].message.tool_calls
        if not tool_calls:
            print("Model answered without a tool call:", first.choices[0].message.content)
            return

        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": tc.arguments},
                    }
                    for tc in tool_calls
                ],
            }
        )
        for tc in tool_calls:
            print(f"Model requested {tc.name}({tc.arguments})")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(
                        {"city": "Paris", "temperature_c": 18, "condition": "Cloudy"}
                    ),
                }
            )

        second = client.chat.completions.create(model=model, messages=messages, max_tokens=200)
        print("Final answer:", second.choices[0].message.content)


if __name__ == "__main__":
    main()
