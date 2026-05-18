"""
llm.py — Groq-based LLM wrapper

All LLM calls go through:
  - ask_json()
  - ask_text()

Requires:
  GROQ_API_KEY in .env or Streamlit secrets
"""

import json
import os
import sys
import time

import streamlit as st
from openai import OpenAI

# ─────────────────────────────────────────────────────────────
# Groq client (OpenAI-compatible SDK)
# ─────────────────────────────────────────────────────────────

client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

MODEL = st.secrets.get("MODEL", "llama-3.3-70b-versatile")

_REWRITE_MARKERS = ("here is a rewritten", "improved version:")


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        newline = text.find("\n")
        text = text[newline + 1:] if newline != -1 else text[3:]
    if text.endswith("```"):
        text = text[: text.rfind("```")].strip()
    return text


def _parse_json(text: str) -> dict:
    start = text.find("{")
    if start != -1:
        obj, _ = json.JSONDecoder().raw_decode(text, start)
        return obj
    return json.loads(text)


def _check_no_rewrite(data, path=""):
    if isinstance(data, dict):
        for k, v in data.items():
            _check_no_rewrite(v, f"{path}.{k}" if path else k)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            _check_no_rewrite(v, f"{path}[{i}]")
    elif isinstance(data, str):
        lower = data.lower()
        for m in _REWRITE_MARKERS:
            if m in lower:
                raise RuntimeError(
                    f"Rewrite violation at {path}: {m}"
                )


# ─────────────────────────────────────────────────────────────
# Core LLM calls
# ─────────────────────────────────────────────────────────────

def ask_json(system: str, user: str, *, temperature=0.0, max_tokens=1500) -> dict:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content or ""
            raw = _strip_fences(raw)

            try:
                parsed = _parse_json(raw)
            except json.JSONDecodeError:
                if attempt < 2:
                    messages.append({"role": "assistant", "content": raw})
                    messages.append({
                        "role": "user",
                        "content": "Return ONLY valid JSON. No markdown, no text."
                    })
                    continue
                raise RuntimeError("Failed to parse JSON from Groq response.")

            _check_no_rewrite(parsed)
            return parsed

        except Exception as e:
            if attempt == 2:
                raise RuntimeError(f"Groq error: {e}")
            time.sleep(1.5 * (attempt + 1))


def ask_text(system: str, user: str, *, temperature=0.0, max_tokens=600) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            if attempt == 2:
                raise RuntimeError(f"Groq error: {e}")
            time.sleep(1.5 * (attempt + 1))