"""
Gap Radar Agent — Detects and clusters student learning gaps.
Scans student utterances for confusion signals and groups them by concept.
When 2+ students struggle with the same concept, fires a common-gap alert.
"""

import logging
import re
from llm_client import call_llm_json

logger = logging.getLogger(__name__)

CONFUSION_PATTERNS = [
    r"don'?t understand", r"don'?t get", r"confused", r"not sure",
    r"how does", r"why does", r"what does.*mean", r"i think.*wrong",
    r"is it.*because", r"can you explain", r"i don'?t know",
    r"mera samajh", r"nahi samajh", r"samajh nahi", r"confuse",
]

_GAP_RADAR_PROMPT = """You are a learning-gap detector in a live classroom.
Analyze these recent STUDENT utterances and identify any conceptual misunderstandings.

Student utterances:
{student_utterances}

Lesson context: {lesson_context}

For each struggling student, identify:
- student_id: the student's ID
- student_name: their name
- concept: the specific concept they're struggling with (e.g., "common denominators", "LCM")
- confusion_type: what kind of confusion (misconception, missing_prerequisite, calculation_error, etc.)
- severity: 1-3 (1=mild, 2=moderate, 3=severe)

Return JSON:
{{
  "gaps": [
    {{"student_id": "...", "student_name": "...", "concept": "...", "confusion_type": "...", "severity": 1}}
  ],
  "common_gaps": [
    {{"concept": "...", "students": ["name1","name2"], "count": 2, "severity": 2}}
  ]
}}

If no gaps detected, return {{"gaps": [], "common_gaps": []}}."""


def detect_confusion_signals(text: str) -> bool:
    """Quick local check for confusion keywords (including Hinglish)."""
    lower = text.lower()
    return any(re.search(p, lower) for p in CONFUSION_PATTERNS)


async def run_gap_radar(state: dict) -> dict:
    transcript = state.get("transcript", [])
    student_utterances = [u for u in transcript[-20:] if u.get("role") == "student"]

    if not student_utterances:
        return state

    # Quick local pre-filter: only call LLM if there are confusion signals
    has_confusion = any(detect_confusion_signals(u.get("text", "")) for u in student_utterances)
    if not has_confusion:
        # Still update student utterance counts
        profiles = state.get("student_profiles", {})
        for u in student_utterances[-5:]:
            sid = u.get("speaker_id", "")
            if sid and sid in profiles:
                profiles[sid]["utterance_count"] = profiles[sid].get("utterance_count", 0) + 1
        state["student_profiles"] = profiles
        return state

    utterance_text = "\n".join(
        f"[{u.get('speaker_id','?')}] {u.get('name','?')}: {u.get('text','')}"
        for u in student_utterances
    )
    lesson_ctx = state.get("lesson_context", "Unknown topic")

    try:
        result = await call_llm_json(
            _GAP_RADAR_PROMPT.format(
                student_utterances=utterance_text,
                lesson_context=lesson_ctx,
            ),
            system="You are a precise learning-gap detector. Always return valid JSON.",
        )

        gaps = result.get("gaps", [])
        common_gaps = result.get("common_gaps", [])

        # Update student profiles with gaps
        profiles = state.get("student_profiles", {})
        for gap in gaps:
            sid = gap.get("student_id", "")
            if sid and sid in profiles:
                concept = gap.get("concept", "")
                if concept and concept not in profiles[sid].get("gaps", []):
                    profiles[sid].setdefault("gaps", []).append(concept)
                profiles[sid]["confusion_signals"] = profiles[sid].get("confusion_signals", 0) + 1
                sev = gap.get("severity", 2)
                profiles[sid]["comprehension_score"] = max(0, profiles[sid].get("comprehension_score", 0.5) - 0.15 * sev)
        state["student_profiles"] = profiles
        state["common_gaps"] = common_gaps

        # Flag if common gap detected (2+ students)
        new_common = [g for g in common_gaps if g.get("count", 0) >= 2]
        if new_common:
            state["gap_alert"] = new_common[0]
            state["agent_log"] = state.get("agent_log", []) + [{
                "agent": "gap_radar", "action": "common_gap_detected", "status": "alert",
                "detail": f"Common gap: {new_common[0].get('concept','?')} — {new_common[0].get('count',0)} students",
            }]
        else:
            state.pop("gap_alert", None)
            state["agent_log"] = state.get("agent_log", []) + [{
                "agent": "gap_radar", "action": "scan", "status": "done",
                "detail": f"Scanned {len(student_utterances)} student utterances, {len(gaps)} individual gaps",
            }]

    except Exception as e:
        logger.error("Gap radar error: %s", e)
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "gap_radar", "action": "scan", "status": "error", "detail": str(e)[:80],
        }]

    return state
