"""
Insights Agent — Post-class summary and learning insights.
Generates per-student gaps, common gaps, who needs support, and recommended next steps.
"""

import logging
from llm_client import call_llm_json

logger = logging.getLogger(__name__)

_INSIGHTS_PROMPT = """You are an educational insights generator. A classroom session just ended.

Lesson context: {lesson_context}
Full transcript ({utterance_count} utterances):
{transcript}

Student profiles:
{student_profiles}

Generate a comprehensive post-class summary:

1. summary: 2-3 sentence overview of what was taught
2. student_insights: per-student analysis
   - student_id, name, level, comprehension_score, gaps (list of concepts), recommendation
3. common_gaps: concepts multiple students struggled with
   - concept, students (list of names), severity, recommended_remediation
4. class_recommendations: 3 actionable next steps for the teacher
5. key_moments: 2-3 notable moments from the class (AI interventions, breakthroughs, etc.)

Return JSON:
{{
  "summary": "...",
  "student_insights": [...],
  "common_gaps": [...],
  "class_recommendations": ["...", "...", "..."],
  "key_moments": [...]
}}"""


async def run_insights(state: dict) -> dict:
    transcript = state.get("transcript", [])
    if not transcript:
        return {"success": False, "error": "No transcript data."}

    # Compact transcript for prompt (last 40 utterances to stay in token budget)
    transcript_text = "\n".join(
        f"[{u.get('role','?')}] {u.get('name','?')}: {u.get('text','')}"
        for u in transcript[-40:]
    )

    profiles = state.get("student_profiles", {})
    profiles_text = "\n".join(
        f"- {p.get('name','?')} (id:{sid}, level:{p.get('level','?')}, "
        f"comprehension:{p.get('comprehension_score',0):.1f}, "
        f"gaps:{p.get('gaps',[])})"
        for sid, p in profiles.items()
    ) or "No student profiles recorded."

    lesson_ctx = state.get("lesson_context", "Unknown topic")

    try:
        result = await call_llm_json(
            _INSIGHTS_PROMPT.format(
                lesson_context=lesson_ctx,
                utterance_count=len(transcript),
                transcript=transcript_text,
                student_profiles=profiles_text,
            ),
            system="You are an expert educational analyst. Always return valid JSON.",
        )

        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "insights", "action": "generate_summary", "status": "done",
            "detail": result.get("summary", "")[:80],
        }]

        return {"success": True, "insights": result}
    except Exception as e:
        logger.error("Insights error: %s", e)
        return {"success": False, "error": str(e)}
