"""
Floor Manager Agent — Turn-taking state machine.
Decides whether the AI is permitted to speak based on who currently has the floor.
"""

import logging
import time

logger = logging.getLogger(__name__)

SILENCE_THRESHOLD_SEC = 2.5
last_speech_ts: float = 0.0


def update_floor_state(state: dict, utterance: dict) -> str:
    """Determine the new floor state from an incoming utterance."""
    global last_speech_ts

    role = utterance.get("role", "")
    if role == "teacher":
        last_speech_ts = time.time()
        return "TEACHER_TALKING"
    elif role == "student":
        last_speech_ts = time.time()
        return "STUDENT_TALKING"
    elif role == "ai":
        return "AI_SPEAKING"
    return state.get("floor_state", "OPEN_FLOOR")


def check_floor_expired() -> bool:
    """Return True if enough silence has elapsed to open the floor."""
    global last_speech_ts
    if last_speech_ts == 0.0:
        return True
    return (time.time() - last_speech_ts) > SILENCE_THRESHOLD_SEC


def can_ai_speak(state: dict) -> bool:
    """The gate: AI may speak only when the floor is open or has expired."""
    if state.get("ai_muted", False):
        return False
    floor = state.get("floor_state", "OPEN_FLOOR")
    if floor == "AI_SPEAKING":
        return True
    if floor in ("TEACHER_TALKING", "STUDENT_TALKING"):
        return check_floor_expired()
    return True


def run_floor_manager(state: dict) -> dict:
    """Evaluate floor state and return whether AI is permitted + current badge."""
    permitted = can_ai_speak(state)
    floor = state.get("floor_state", "OPEN_FLOOR")

    badges = {
        "TEACHER_TALKING": "🟦 Teacher speaking",
        "STUDENT_TALKING": "🟩 Student speaking",
        "OPEN_FLOOR": "⬜ Open floor",
        "AI_SPEAKING": "🟪 AI speaking",
    }

    state["floor_state"] = "OPEN_FLOOR" if (permitted and floor != "AI_SPEAKING") else floor
    state["ai_permitted"] = permitted
    state["floor_badge"] = badges.get(floor, badges["OPEN_FLOOR"])
    return state
