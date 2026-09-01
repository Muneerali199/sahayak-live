"""
Multi-Agent Classroom Co-Teacher - LLM Client
Provider chain: Groq -> Mistral -> Local Ollama (offline).
Groq/Mistral are fast cloud LLMs; Ollama runs fully locally with no API key.
"""

import os
import json
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
# Local model settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "1") == "1"

_lazy_gemini = None


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
    """Call Groq via raw HTTP so we fail fast on rate limits instead of
    blocking on long automatic retries — the fallback chain handles retries."""
    import httpx

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    # Short timeout so a rate-limit / outage fails fast and we can fall back
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        if resp.status_code != 200:
            raise ValueError(f"Groq API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def call_ollama(prompt: str, system: str = "", model: str | None = None) -> str:
    """Call a fully-local LLM via Ollama. Works with no API key / no internet."""
    import httpx

    if not OLLAMA_ENABLED:
        raise ValueError("OLLAMA_ENABLED is false")

    use_model = model or OLLAMA_MODEL
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    payload = {
        "model": use_model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 600},
    }
    last_error = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
                if resp.status_code != 200:
                    last_error = ValueError(f"Ollama HTTP {resp.status_code}: {resp.text[:200]}")
                    await asyncio.sleep(1.0)
                    continue
                data = resp.json()
                text = data.get("response", "").strip()
                if not text:
                    raise ValueError("Ollama returned empty response")
                return text
        except httpx.HTTPError as e:
            last_error = e
            await asyncio.sleep(1.0)
    raise last_error or ValueError("Ollama request failed")


def ollama_healthy() -> bool:
    """Check whether the local Ollama server is reachable."""
    try:
        import httpx
        if not OLLAMA_ENABLED:
            return False
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def has_cloud() -> bool:
    """True if any cloud key is configured."""
    return bool(GROQ_API_KEY or MISTRAL_API_KEY or GEMINI_API_KEY)



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
    """Call an LLM, chaining Groq -> Mistral -> local Ollama so it always works."""
    provider = resolve_provider(model)
    errors = []
    try:
        if provider == "groq":
            return await call_groq(prompt, system)
        if provider == "mistral":
            return await call_mistral(prompt, system)
        return await call_gemini(prompt, system)
    except Exception as e:
        errors.append((provider, e))
        logger.warning("Primary provider %s failed (%s), trying fallbacks", provider, e)

    # Fallback 1: the other cloud (if the primary wasn't Groq, try Groq; else try Mistral)
    for fb in (["groq", "mistral"] if provider != "groq" else ["mistral", "gemini"]):
        try:
            if fb == "groq":
                return await call_groq(prompt, system)
            if fb == "mistral":
                return await call_mistral(prompt, system)
            if fb == "gemini":
                return await call_gemini(prompt, system)
        except Exception as e2:
            errors.append((fb, e2))
            logger.warning("Fallback %s failed (%s)", fb, e2)

    # Fallback 2: local Ollama (fully offline, no key needed)
    if ollama_healthy():
        try:
            logger.warning("Using LOCAL Ollama (%s) as fallback", OLLAMA_MODEL)
            return await call_ollama(prompt, system)
        except Exception as e3:
            errors.append(("ollama", e3))
            logger.warning("Local Ollama fallback failed: %s", e3)

    raise errors[-1][1] if errors else ValueError("No LLM provider available")


def resolve_provider(model: str) -> str:
    """Pick the primary provider. Prefers fast cloud, then falls back locally.
    Returns the resolved provider for this request."""
    if model == "groq":
        if GROQ_API_KEY:
            return "groq"
        if MISTRAL_API_KEY:
            return "mistral"
        return "ollama"
    if model == "mistral":
        if MISTRAL_API_KEY:
            return "mistral"
        if GROQ_API_KEY:
            return "groq"
        return "ollama"
    # default ("gemini")
    if GEMINI_API_KEY:
        return "gemini"
    if GROQ_API_KEY:
        return "groq"
    if MISTRAL_API_KEY:
        return "mistral"
    return "ollama"


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

    async def _try(fn, label):
        try:
            raw = await fn(prompt, system)
            parsed = json.loads(_repair_json(raw.strip()))
            return parsed
        except Exception as e:
            logger.warning("%s failed in call_llm_json (%s)", label, e)
            return None

    # Try primary, then other cloud, then local Ollama
    if provider == "groq":
        chain = [call_groq, call_mistral, call_ollama]
    elif provider == "mistral":
        chain = [call_mistral, call_groq, call_ollama]
    elif provider == "gemini":
        chain = [call_gemini, call_groq, call_mistral, call_ollama]
    else:
        chain = [call_ollama, call_groq, call_mistral]

    for fn in chain:
        if fn is call_ollama and not ollama_healthy():
            continue
        if fn in (call_groq,) and not GROQ_API_KEY:
            continue
        if fn in (call_mistral,) and not MISTRAL_API_KEY:
            continue
        if fn in (call_gemini,) and not GEMINI_API_KEY:
            continue
        parsed = await _try(fn, fn.__name__)
        if parsed is not None:
            return parsed

    logger.warning("Failed to get parsesable JSON from any LLM provider")
    return {"content": ""}
