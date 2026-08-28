"""
Differentiation Agent — Maintains per-student comprehension levels.
Decides which explanation level (beginner/intermediate/advanced) to use for each student.
"""

import logging
from llm_client import call_llm_json

logger = logging.getLogger(__name__)

_DIFFERENTIATION_PROMPT = """You are a differentiation engine in a live classroom.
Based on a student's recent utterances, assess their comprehension level.

Student name: {name}
Recent utterances: {utterances}
Lesson context: {lesson_context}

Assess:
- level: "beginner", "intermediate", or "advanced"
- confidence: 0.0-1.0 (how confident you are in this assessment)
- reasoning: one sentence explaining why

Return JSON: {{"level": "...", "confidence": 0.0, "reasoning": "..."}}"""


async def run_differentiation(state: dict) -> dict:
    transcript = state.get("transcript", [])
    profiles = state.get("student_profiles", {})

    # Only re-assess students who have spoken recently
    recent_student_ids = set()
    for u in transcript[-10:]:
        if u.get("role") == "student":
            recent_student_ids.add(u.get("speaker_id", ""))

    for sid in recent_student_ids:
        if sid not in profiles:
            continue
        student_utterances = [
            u for u in transcript
            if u.get("speaker_id") == sid and u.get("role") == "student"
        ][-5:]

        if len(student_utterances) < 2:
            continue

        utterance_text = "; ".join(u.get("text", "") for u in student_utterances)
        name = profiles[sid].get("name", sid)

        try:
            result = await call_llm_json(
                _DIFFERENTIATION_PROMPT.format(
                    name=name,
                    utterances=utterance_text,
                    lesson_context=state.get("lesson_context", "Unknown"),
                ),
                system="You are a student comprehension assessor. Always return valid JSON.",
            )
            new_level = result.get("level", profiles[sid].get("level", "intermediate"))
            profiles[sid]["level"] = new_level
            profiles[sid]["confidence"] = result.get("confidence", 0.5)
        except Exception as e:
            logger.warning("Differentiation error for %s: %s", sid, e)

    state["student_profiles"] = profiles
    return state


def get_explanation_level(profile: dict) -> str:
    """Helper: get the explanation level for a student."""
    return profile.get("level", "intermediate")
