"""
Quizmaster Agent — Conducts spoken quizzes.
Asks questions out loud, names a student, listens for the answer, evaluates.
"""

import logging
from llm_client import call_llm, call_llm_json

logger = logging.getLogger(__name__)

_QUIZ_GEN_PROMPT = """You are Sahayak, a quizmaster in a live classroom.

Lesson context: {lesson_context}
Target student: {student_name} (level: {level})

Generate ONE quiz question that:
- Tests a concept from the current lesson
- Is appropriate for the student's level
- Can be answered verbally in one sentence
- Is NOT a yes/no question

Return JSON: {{"question": "...", "expected_answer": "...", "concept_tested": "..."}}"""

_QUIZ_EVAL_PROMPT = """You are evaluating a student's quiz answer.

Question asked: {question}
Expected answer: {expected_answer}
Student's answer: {student_answer}
Student name: {student_name}

Evaluate:
- correct: true/false/partially
- feedback: one sentence of encouraging feedback (address student by name)
- score: 0-100

Return JSON: {{"correct": "...", "feedback": "...", "score": 0}}"""


async def generate_quiz_question(state: dict, target_student_id: str) -> dict:
    """Generate a quiz question for a specific student."""
    profiles = state.get("student_profiles", {})
    profile = profiles.get(target_student_id, {})
    name = profile.get("name", "student")
    level = profile.get("level", "intermediate")
    lesson_ctx = state.get("lesson_context", "Unknown topic")

    try:
        result = await call_llm_json(
            _QUIZ_GEN_PROMPT.format(
                lesson_context=lesson_ctx,
                student_name=name,
                level=level,
            ),
            system="You are a quiz question generator. Always return valid JSON.",
        )
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "quizmaster", "action": "generate_question", "status": "done",
            "detail": f"Q for {name}: {result.get('question','')[:60]}",
        }]
        return result
    except Exception as e:
        logger.error("Quiz gen error: %s", e)
        return {"question": "", "expected_answer": "", "concept_tested": ""}


async def evaluate_quiz_answer(
    state: dict,
    question: str,
    expected_answer: str,
    student_answer: str,
    student_name: str,
) -> dict:
    """Evaluate a student's quiz answer."""
    try:
        result = await call_llm_json(
            _QUIZ_EVAL_PROMPT.format(
                question=question,
                expected_answer=expected_answer,
                student_answer=student_answer,
                student_name=student_name,
            ),
            system="You are a quiz evaluator. Always return valid JSON.",
        )
        state["agent_log"] = state.get("agent_log", []) + [{
            "agent": "quizmaster", "action": "evaluate", "status": "done",
            "detail": f"{student_name}: {result.get('correct','')} ({result.get('score',0)}/100)",
        }]
        return result
    except Exception as e:
        logger.error("Quiz eval error: %s", e)
        return {"correct": "unknown", "feedback": "Could not evaluate.", "score": 50}
