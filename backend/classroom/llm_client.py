"""
Multi-Agent Interview Copilot - LLM Client
Handles communication with Gemini (free tier) and Groq (free tier).
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

_lazy_gemini = None
_lazy_groq = None


def _get_gemini():
    global _lazy_gemini
    if _lazy_gemini is None:
        from langchain_google_genai import ChatGoogleGenerativeAI
        _lazy_gemini = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=GEMINI_API_KEY,
            temperature=0.7,
            max_output_tokens=4096,
        )
    return _lazy_gemini


def _get_groq():
    global _lazy_groq
    if _lazy_groq is None:
        from langchain_groq import ChatGroq
        _lazy_groq = ChatGroq(
            model="openai/gpt-oss-120b",
            groq_api_key=GROQ_API_KEY,
            temperature=0.3,
            max_tokens=4096,
        )
    return _lazy_groq


async def call_gemini(prompt: str, system: str = "") -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    llm = _get_gemini()
    messages = []
    if system:
        messages.append(("system", system))
    messages.append(("human", prompt))
    resp = await llm.ainvoke(messages)
    return resp.content


async def call_groq(prompt: str, system: str = "") -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    llm = _get_groq()
    messages = []
    if system:
        messages.append(("system", system))
    messages.append(("human", prompt))
    resp = await llm.ainvoke(messages)
    return resp.content


async def call_mistral(prompt: str, system: str = "") -> str:
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not set")
    import asyncio

    import httpx

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "mistral-small-latest",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code in (429, 500, 502, 503, 504):
                    last_error = ValueError(f"Mistral API error {resp.status_code}: {resp.text[:200]}")
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                if resp.status_code != 200:
                    raise ValueError(f"Mistral API error {resp.status_code}: {resp.text[:300]}")
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            last_error = e
            await asyncio.sleep(1.5 * (attempt + 1))
    raise last_error or ValueError("Mistral API request failed")


async def call_llm(prompt: str, system: str = "", model: str = "gemini") -> str:
    provider = resolve_provider(model)
    if provider == "groq":
        return await call_groq(prompt, system)
    if provider == "mistral":
        return await call_mistral(prompt, system)
    return await call_gemini(prompt, system)


def resolve_provider(model: str) -> str:
    """Pick which provider actually runs, with automatic fallback."""
    if model == "groq":
        return "groq" if GROQ_API_KEY else "mistral"
    if model == "mistral":
        return "mistral" if MISTRAL_API_KEY else "groq"
    # default gemini request -> gemini, else mistral, else groq
    if GEMINI_API_KEY:
        return "gemini"
    if MISTRAL_API_KEY:
        return "mistral"
    if GROQ_API_KEY:
        return "groq"
    raise ValueError("No LLM API key configured (set GEMINI_API_KEY, MISTRAL_API_KEY, or GROQ_API_KEY)")


def _repair_json(text: str) -> str:
    import re

    # Strip code fences if any
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    # Remove trailing commas before } or ] (common Mistral artifact)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    # Drop any trailing text after the final closing brace/bracket
    start = text.find("{")
    if start == -1:
        start = text.find("[")
    if start != -1:
        # find matching last close
        end = max(text.rfind("}"), text.rfind("]"))
        if end > start:
            text = text[start:end + 1]
    return text


async def call_llm_json(prompt: str, system: str = "", model: str = "gemini") -> dict:
    provider = resolve_provider(model)
    try:
        raw = None
        if provider == "groq":
            raw = await call_groq(prompt, system)
        elif provider == "mistral":
            raw = await call_mistral(prompt, system)
        else:
            raw = await call_gemini(prompt, system)
        text = _repair_json(raw.strip())
        return json.loads(text)
    except (json.JSONDecodeError, ValueError, Exception) as e:
        # Fall back to Groq (clean JSON) when the primary provider fumbles
        if provider != "groq" and GROQ_API_KEY:
            try:
                logger.warning("Primary provider failed (%s), retrying via Groq", e)
                raw2 = await call_groq(prompt, system)
                text2 = _repair_json(raw2.strip())
                return json.loads(text2)
            except Exception as e2:
                logger.warning("Groq fallback failed: %s", e2)
        raw = raw or ""
        logger.warning("Failed to parse JSON from LLM: %s", raw[:200])
        return {"content": raw}
