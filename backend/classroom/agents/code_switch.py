"""
Code-Switch Agent — Detects language mixing in the classroom and
ensures the AI responds in the matching language/register.

Mistral is particularly good at Hinglish and Indian language code-switching.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Detect common Indian language markers in otherwise-English text
INDIC_MARKERS = [
    (r"\b(nahi|nahin|haan|theek|thik|acha|achha|kya|kyun|kaise|matlab|samajh|bhai|yaar|bahut|bohot|thoda|zyada|kam)\b", "hi"),
    (r"\b(illa|illa|haan|saaptiya|saapta|puriyala|puriyatha|enna|eppadi)\b", "ta"),
    (r"\b(kadu|ledu|ante|emi|cheppu|telusu)\b", "te"),
    (r"\b(nahi|ho|ahe|kaay|kasa)\b", "mr"),
    (r"\b(na|hae|ki|bolchi)\b", "bn"),
]


def detect_language(text: str) -> str:
    """Detect the dominant language or code-switch pattern in an utterance."""
    if not text:
        return "en"
    lower = text.lower()
    for pattern, lang in INDIC_MARKERS:
        if re.search(pattern, lower):
            return lang
    return "en"


def detect_classroom_language(transcript: list[dict]) -> str:
    """Detect the dominant language across recent utterances."""
    if not transcript:
        return "en"
    recent = transcript[-10:]
    lang_counts: dict[str, int] = {}
    for u in recent:
        lang = detect_language(u.get("text", ""))
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    # If any Indic language appears 2+ times, use it
    for lang, count in lang_counts.items():
        if lang != "en" and count >= 2:
            return lang
    return "en"


def get_language_instruction(lang: str) -> str:
    """Return an instruction string for the LLM about how to respond."""
    lang_names = {
        "hi": "Hindi (you may code-switch between Hindi and English — Hinglish is encouraged)",
        "ta": "Tamil (you may code-switch between Tamil and English)",
        "te": "Telugu (you may code-switch between Telugu and English)",
        "mr": "Marathi (you may code-switch between Marathi and English)",
        "bn": "Bengali (you may code-switch between Bengali and English)",
    }
    return lang_names.get(lang, "English")


def run_code_switch(state: dict) -> dict:
    """Update the classroom language state based on recent transcript."""
    transcript = state.get("transcript", [])
    lang = detect_classroom_language(transcript)
    old_lang = state.get("language", "en")
    if lang != old_lang:
        state["language"] = lang
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "code_switch", "action": "language_change", "status": "done",
            "detail": f"Classroom language: {old_lang} → {lang}",
        }]
    return state
