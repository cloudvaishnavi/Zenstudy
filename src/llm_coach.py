"""
src/llm_coach.py — Optional AI Study Coach using OpenAI-compatible API.
Requires OPENAI_API_KEY env var. Optional: OPENAI_BASE_URL, OPENAI_MODEL.
"""
from __future__ import annotations

import os
import requests


def is_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def ask_coach(question: str, context_csv: str) -> str:
    """
    Send question + recent session context to the LLM.
    Returns the coach's response as a string.
    """
    api_key  = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model    = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    url      = f"{base_url}/chat/completions"

    system_prompt = (
        "You are an expert, encouraging study coach. "
        "The user shares their recent study session data as a CSV. "
        "Give specific, actionable, data-driven advice. "
        "Be concise, warm, and motivating. Use bullet points where helpful."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Here is my recent study data:\n\n```\n{context_csv}\n```\n\n"
                    f"My question: {question}"
                ),
            },
        ],
        "temperature": 0.4,
        "max_tokens": 600,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
