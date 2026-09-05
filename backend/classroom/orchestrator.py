"""
Sahayak Live — Classroom Orchestrator
LangGraph StateGraph that coordinates all 7 agents in real-time.
"""

import sys
import os
import logging
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import ClassroomState
from tts import detect_language as detect_lang
from agents.floor_manager import run_floor_manager, update_floor_state
from agents.lesson_context import run_lesson_context
from agents.code_switch import run_code_switch
from agents.gap_radar import run_gap_radar
from agents.differentiation import run_differentiation
from agents.explainer import run_explainer
from agents.replier import run_replier
from agents.quizmaster import generate_quiz_question, evaluate_quiz_answer
from agents.insights import run_insights

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available, using sequential fallback")


# ─── Graph Nodes ───────────────────────────────────────────────────

async def ingest_node(state: dict) -> dict:
    """Append the latest utterance to transcript and update floor state."""
    utterance = state.get("last_utterance")
    if not utterance:
        return state

    transcript = state.get("transcript", [])
    transcript.append(utterance)
    state["transcript"] = transcript[-50:]  # keep last 50

    new_floor = update_floor_state(state, utterance)
    state["floor_state"] = new_floor
    state["current_speaker_id"] = utterance.get("speaker_id", "")
    state["current_speaker_role"] = utterance.get("role", "")

    # Auto-match the student's language so every agent + voice replies in it
    state["language"] = detect_lang(utterance.get("text", ""))

    # Register student profile if new
    if utterance.get("role") == "student":
        sid = utterance.get("speaker_id", "")
        profiles = state.get("student_profiles", {})
        if sid not in profiles:
            profiles[sid] = {
                "student_id": sid,
                "name": utterance.get("name", sid),
                "level": "intermediate",
                "gaps": [],
                "comprehension_score": 0.5,
                "utterance_count": 1,
                "confusion_signals": 0,
            }
        else:
            profiles[sid]["utterance_count"] = profiles[sid].get("utterance_count", 0) + 1
        state["student_profiles"] = profiles

    return state


async def context_node(state: dict) -> dict:
    return await run_lesson_context(state)


async def codeswitch_node(state: dict) -> dict:
    return run_code_switch(state)


async def gapradar_node(state: dict) -> dict:
    return await run_gap_radar(state)


async def differentiation_node(state: dict) -> dict:
    return await run_differentiation(state)


async def floormanager_node(state: dict) -> dict:
    return run_floor_manager(state)


async def router_node(state: dict) -> dict:
    """Decide what action the AI should take (if any)."""
    ai_muted = state.get("ai_muted", False)

    # A direct student question is answered promptly (the student just ceded the floor),
    # provided the AI isn't muted — this lets the AI reply to "hello"/questions.
    last = state.get("last_utterance", {})
    last_text = last.get("text", "").lower().strip()
    last_role = last.get("role", "")
    direct_query = (not ai_muted and last_role in ("student", "teacher") and _is_direct_query(last_text))

    if not (state.get("ai_permitted", False) or direct_query):
        state["pending_action"] = None
        return state

    # Priority 1: Teacher-requested quiz
    if state.get("quiz_request"):
        target = state.get("quiz_request", "")
        state.pop("quiz_request", None)
        quiz = await generate_quiz_question(state, target)
        if quiz.get("question"):
            state["quiz_active"] = True
            state["quiz_target_student"] = target
            state["quiz_question"] = quiz["question"]
            state["quiz_answer"] = quiz.get("expected_answer", "")
            state["pending_action"] = {
                "type": "QUIZ_ASK",
                "target_student_id": target,
                "content": quiz["question"],
                "concept": quiz.get("concept_tested", ""),
            }
            return state

    # Priority 2: Quiz answer pending evaluation
    if state.get("quiz_answer_pending"):
        pending = state.pop("quiz_answer_pending", {})
        result = await evaluate_quiz_answer(
            state,
            question=pending.get("question", ""),
            expected_answer=pending.get("expected_answer", ""),
            student_answer=pending.get("student_answer", ""),
            student_name=pending.get("student_name", "student"),
        )
        state["quiz_active"] = False
        feedback = result.get("feedback", "Good try!")
        score = result.get("score", 50)
        state["pending_action"] = {
            "type": "QUIZ_EVALUATE",
            "content": feedback,
            "score": score,
            "correct": result.get("correct", ""),
        }
        return state

    # Priority 3: Common gap detected → broadcast explanation
    gap_alert = state.get("gap_alert")
    if gap_alert:
        concept = gap_alert.get("concept", "")
        if concept:
            state.pop("gap_alert", None)
            spoken = await run_explainer(state, concept, is_whisper=False)
            if spoken:
                state["pending_action"] = {
                    "type": "EXPLAIN",
                    "content": spoken,
                    "concept": concept,
                }
                return state

    # Priority 4: Individual student confusion → whisper
    profiles = state.get("student_profiles", {})
    for sid, profile in profiles.items():
        if profile.get("confusion_signals", 0) >= 2 and profile.get("gaps"):
            concept = profile["gaps"][-1]
            # Don't repeat if already addressed
            if concept not in state.get("addressed_whispers", []):
                spoken = await run_explainer(state, concept, target_student_id=sid, is_whisper=True)
                if spoken:
                    state.setdefault("addressed_whispers", []).append(concept)
                    state["pending_action"] = {
                        "type": "WHISPER_EXPLAIN",
                        "target_student_id": sid,
                        "content": spoken,
                        "concept": concept,
                    }
                    return state

    # Priority 5: Direct conversational reply to a student query
    if direct_query:
        spoken = await run_replier(state)
        if spoken:
            state["pending_action"] = {
                "type": "EXPLAIN",
                "content": spoken,
                "concept": "direct reply",
            }
            return state

    state["pending_action"] = None
    return state


def _is_direct_query(text: str) -> bool:
    """Heuristic: does this utterance look like a direct question or greeting
    aimed at the AI, rather than normal class narration?"""
    markers = (
        "sahayak", "hey", "hello", "hi ", "?" ,
        "explain", "help", "what is", "what's", "how do", "can you",
        "i don't understand", "i dont understand", "i do not understand", "don't get", "dont get",
        "confused", "please", "anyone", "teacher?",
    )
    return any(m in text for m in markers)


async def action_node(state: dict) -> dict:
    """Execute the pending action (the action itself is sent by main.py via WebSocket)."""
    action = state.get("pending_action")
    if action:
        state["last_action"] = action.get("type", "NONE")
        state["floor_state"] = "AI_SPEAKING"
    else:
        state["last_action"] = "NONE"
    return state


# ─── Build the Graph ───────────────────────────────────────────────

def build_graph():
    """Build and compile the LangGraph StateGraph."""
    if not LANGGRAPH_AVAILABLE:
        return None

    g = StateGraph(ClassroomState)
    g.add_node("ingest", ingest_node)
    g.add_node("context", context_node)
    g.add_node("codeswitch", codeswitch_node)
    g.add_node("gapradar", gapradar_node)
    g.add_node("differentiation", differentiation_node)
    g.add_node("floormanager", floormanager_node)
    g.add_node("router", router_node)
    g.add_node("action", action_node)

    g.set_entry_point("ingest")
    g.add_edge("ingest", "context")
    g.add_edge("context", "codeswitch")
    g.add_edge("codeswitch", "gapradar")
    g.add_edge("gapradar", "differentiation")
    g.add_edge("differentiation", "floormanager")
    g.add_edge("floormanager", "router")
    g.add_edge("router", "action")
    g.add_edge("action", END)

    return g.compile()


async def run_sequential(state: dict) -> dict:
    """Sequential fallback if LangGraph is not available."""
    state = await ingest_node(state)
    state = await context_node(state)
    state = run_code_switch(state)
    state = await gapradar_node(state)
    state = await differentiation_node(state)
    state = run_floor_manager(state)
    state = await router_node(state)
    state = await action_node(state)
    return state


# ─── Public API ────────────────────────────────────────────────────

_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def process_utterance(state: dict) -> dict:
    """Process a single utterance through the full agent pipeline."""
    graph = get_graph()
    if graph:
        try:
            return await graph.ainvoke(state)
        except Exception as e:
            logger.error("Graph execution error, falling back: %s", e)
            return await run_sequential(state)
    return await run_sequential(state)


async def generate_insights(state: dict) -> dict:
    """Generate post-class insights."""
    return await run_insights(state)
