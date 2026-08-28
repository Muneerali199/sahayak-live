"""
Lesson Context Agent — Maintains a rolling understanding of the ongoing lesson.
Summarizes what topic is being taught, what concepts have been covered,
and what the current focus is.
"""

import logging
from llm_client import call_llm

logger = logging.getLogger(__name__)

LESSON_CONTEXT_PROMPT = """You are a lesson context tracker in a live classroom.
Given the recent transcript, produce a concise summary of:
1. The subject and topic being taught
2. Key concepts covered so far
3. The current focus / what the teacher is explaining right now

Keep it under 120 words. This is internal context for other AI agents — not spoken to students.

Transcript (most recent first, last 15 utterances):
{transcript}

Current context (update if stale): {current_context}

Respond with ONLY the updated context summary, no JSON, no markdown."""


async def run_lesson_context(state: dict) -> dict:
    transcript = state.get("transcript", [])[-15:]
    if not transcript:
        return state

    transcript_text = "\n".join(
        f"[{u.get('role','?')}] {u.get('name','?')}: {u.get('text','')}"
        for u in transcript
    )

    current = state.get("lesson_context", "No context yet.")

    try:
        summary = await call_llm(
            LESSON_CONTEXT_PROMPT.format(transcript=transcript_text, current_context=current),
            system="You are a concise classroom context tracker.",
        )
        state["lesson_context"] = summary.strip()
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "lesson_context", "action": "summarize", "status": "done",
            "detail": summary.strip()[:80],
        }]
    except Exception as e:
        logger.error("Lesson context error: %s", e)
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "lesson_context", "action": "summarize", "status": "error",
            "detail": str(e)[:80],
        }]

    return state
