"""
Explainer Agent — Generates explanations at different difficulty levels.
Can broadcast to the whole class or whisper privately to one student.
"""

import logging
from llm_client import call_llm

logger = logging.getLogger(__name__)

_EXPLAIN_PROMPT = """You are Sahayak, a friendly AI co-teacher in a live classroom.

Lesson context: {lesson_context}
Concept to explain: {concept}
Explanation level: {level} ({level_hint})
Target student: {student_name} (address them by name)

{language_instruction}

Rules:
- Keep it under 80 words (this is spoken aloud, not read).
- Use a relatable example appropriate for the level.
- Be warm and encouraging.
- If broadcasting to the class, say "class" or address the student by name.
- If this is a private whisper, start with "{student_name}, let me help you understand..."

Produce ONLY the spoken text. No JSON, no markdown, no stage directions."""


_LEVEL_HINTS = {
    "beginner": "very simple language, concrete everyday examples, step-by-step, avoid jargon entirely",
    "intermediate": "clear academic language, one analogy, introduce key terms with brief definitions",
    "advanced": "precise terminology, abstract reasoning, connect to broader concepts, challenge the student",
}


async def run_explainer(
    state: dict,
    concept: str,
    target_student_id: str | None = None,
    is_whisper: bool = False,
) -> str:
    """Generate an explanation. If target_student_id is set, calibrate to their level."""
    profiles = state.get("student_profiles", {})
    lesson_ctx = state.get("lesson_context", "Unknown topic")

    if target_student_id and target_student_id in profiles:
        level = profiles[target_student_id].get("level", "intermediate")
        student_name = profiles[target_student_id].get("name", "student")
    else:
        level = "intermediate"
        student_name = "class"

    # Language instruction
    lang = state.get("language", "en")
    if lang and lang != "en":
        language_instruction = f"Speak in {lang}. You may code-switch between {lang} and English naturally."
    else:
        language_instruction = "Speak in English. If students use Hinglish or other Indian languages, match their style."

    level_hint = _LEVEL_HINTS.get(level, _LEVEL_HINTS["intermediate"])

    prompt = _EXPLAIN_PROMPT.format(
        lesson_context=lesson_ctx,
        concept=concept,
        level=level,
        level_hint=level_hint,
        student_name=student_name,
        language_instruction=language_instruction,
    )

    try:
        text = await call_llm(prompt, system="You are Sahayak, a warm and patient AI co-teacher for Indian classrooms.")
        spoken = text.strip()

        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "explainer",
            "action": "whisper" if is_whisper else "explain",
            "status": "done",
            "detail": f"[{level}] {concept} → {student_name}: {spoken[:60]}",
        }]
        return spoken
    except Exception as e:
        logger.error("Explainer error: %s", e)
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "explainer", "action": "explain", "status": "error", "detail": str(e)[:80],
        }]
        return ""
