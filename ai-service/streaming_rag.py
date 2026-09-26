import json
import os

import httpx
from dotenv import load_dotenv


load_dotenv()


OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

MODEL_NAME = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)


async def generate_answer_stream(
    prompt: str
):
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY is missing."
        )

    headers = {
        "Authorization":
            f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":
            "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "temperature": 0.2,
        "max_tokens": 300,
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    timeout = httpx.Timeout(
        60.0,
        connect=10.0
    )

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:

        async with client.stream(
            "POST",
            OPENROUTER_URL,
            headers=headers,
            json=payload
        ) as response:

            response.raise_for_status()

            async for line in response.aiter_lines():

                if not line:
                    continue

                if not line.startswith("data:"):
                    continue

                data_text = line[
                    len("data:"):
                ].strip()

                if data_text == "[DONE]":
                    break

                try:
                    data = json.loads(
                        data_text
                    )

                except json.JSONDecodeError:
                    continue

                choices = data.get(
                    "choices",
                    []
                )

                if not choices:
                    continue

                delta = choices[0].get(
                    "delta",
                    {}
                )

                content = delta.get(
                    "content"
                )

                if content:
                    yield content