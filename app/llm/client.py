from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

from llm.demo_client import call_demo_llm


MODEL_NAME = "gpt-4.1"
TEMPERATURE = 0.7
_DEMO_MODE = False


load_dotenv()


def has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def configure_client_mode(*, force_demo: bool = False) -> bool:
    global _DEMO_MODE
    _DEMO_MODE = force_demo or not has_api_key()
    return _DEMO_MODE


def _build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Ensure .env exists in project root and contains OPENAI_API_KEY=..."
        )
    return OpenAI(api_key=api_key)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    if _DEMO_MODE or not has_api_key():
        return call_demo_llm(system_prompt, user_prompt)
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
