"""
Replier Agent — Generates a direct conversational response.
Handles general student questions, greetings, and direct queries
when no higher-priority action (quiz/gap/whisper) is pending.
"""

import logging
from llm_client import call_llm

logger = logging.getLogger(__name__)

_REPLY_PROMPT = """You are Sahayak, a friendly AI co-teacher in a live classroom.

Lesson context: {lesson_context}
The student just said: "{student_text}"
Speaker: {speaker_name} ({speaker_role})

{language_instruction}

Rules:
- Respond directly and helpfully to what they just said or asked.
- If it is a greeting or casual remark, greet back warmly and briefly nudge the lesson along.
- If it is a genuine question, answer it clearly and concisely.
- Keep it under 70 words (this is spoken aloud, not read).
- Use a relatable example if helpful.
- Address the speaker by name.
- Do not interrupt the teacher; only speak because the floor is currently open.

Produce ONLY the spoken text. No JSON, no markdown, no stage directions."""


async def run_replier(state: dict) -> str | None:
    """Generate a direct conversational reply to the latest utterance."""
    last = state.get("last_utterance")
    if not last:
        return None

    student_text = last.get("text", "")
    speaker_name = last.get("name", "student")
    speaker_role = last.get("role", "student")

    # Don't reply to AI messages
    if speaker_role == "ai":
        return None

    lesson_ctx = state.get("lesson_context", "Unknown topic")

    lang = state.get("language", "en")
    if lang and lang != "en":
        language_instruction = f"Speak in {lang}. You may code-switch between {lang} and English naturally."
    else:
        language_instruction = "Speak in English. If students use Hinglish or other Indian languages, match their style."

    prompt = _REPLY_PROMPT.format(
        lesson_context=lesson_ctx,
        student_text=student_text,
        speaker_name=speaker_name,
        speaker_role=speaker_role,
        language_instruction=language_instruction,
    )

    try:
        text = await call_llm(
            prompt,
            system="You are Sahayak, a warm and patient AI co-teacher for Indian classrooms.",
        )
        spoken = text.strip()
        if not spoken:
            return None
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "replier",
            "action": "reply",
            "status": "done",
            "detail": f"replied to {speaker_name}: {spoken[:60]}",
        }]
        return spoken
    except Exception as e:
        logger.error("Replier error: %s", e)
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "replier", "action": "reply", "status": "error", "detail": str(e)[:80],
        }]
        return None
