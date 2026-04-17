from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI


MODEL_NAME = "gpt-4.1"
TEMPERATURE = 0.7


load_dotenv()


def _build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Ensure .env exists in project root and contains OPENAI_API_KEY=..."
        )
    return OpenAI(api_key=api_key)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    client = _build_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI API returned an empty response.")
    return content
