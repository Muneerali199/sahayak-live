"""
Sahayak Live — FastAPI Backend
WebSocket room manager + multi-agent orchestrator for live classroom.
"""

import sys
import os
import json
import io
import uuid
import logging
import subprocess
import tempfile
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from room import registry, Room, Participant
from orchestrator import process_utterance, generate_insights
from llm_client import GROQ_API_KEY, MISTRAL_API_KEY, ollama_healthy
from tts import synthesize as tts_synthesize, _piper_available as piper_available

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Sahayak Live — Multi-Agent Co-Teacher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory room states ─────────────────────────────────────────

room_states: dict[str, dict] = {}


def get_room_state(room_id: str) -> dict:
    """Get or initialize the ClassroomState for a room."""
    if room_id not in room_states:
        room_states[room_id] = {
            "room_id": room_id,
            "transcript": [],
            "floor_state": "OPEN_FLOOR",
            "current_speaker_id": "",
            "current_speaker_role": "",
            "lesson_context": "",
            "lesson_topic": "",
            "student_profiles": {},
            "common_gaps": [],
            "pending_actions": [],
            "last_action": "NONE",
            "ai_muted": False,
            "session_active": True,
            "agent_log": [],
            "language": "en",
            "quiz_active": False,
            "quiz_target_student": "",
            "quiz_question": "",
            "quiz_answer": "",
            "addressed_whispers": [],
            "approve_mode": False,
        }
    return room_states[room_id]


# ─── Local TTS (neural Piper, falls back to macOS `say`) ──────────

TTS_VOICE = os.getenv("TTS_VOICE", "Rishi")  # fallback macOS voice


@app.get("/api/tts")
async def synthesize_speech(text: str, lang: str = "en-IN"):
    """Generate human-like speech audio via local neural TTS. Returns a WAV file."""
    if not text:
        return {"error": "No text provided"}, 400

    try:
        audio, media_type = tts_synthesize(text)
        return Response(
            content=audio,
            media_type=media_type,
            headers={
                "X-TTS-Engine": "piper" if piper_available() else "say",
                "X-TTS-Text-Length": str(len(text)),
            },
        )
    except Exception as e:
        logger.error("TTS error: %s", e)
        return {"error": f"TTS failed: {e}"}, 500


# ─── REST Endpoints ────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "Sahayak Live — Multi-Agent Co-Teacher",
        "groq_configured": bool(GROQ_API_KEY),
        "mistral_configured": bool(MISTRAL_API_KEY),
        "local_ollama": ollama_healthy(),
        "active_rooms": len(registry.rooms),
    }


@app.get("/api/rooms")
async def list_rooms():
    return {"rooms": registry.list_rooms()}


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    room = registry.get_room(room_id)
    if not room:
        return {"error": "Room not found"}, 404
    return room.summary()


@app.post("/api/rooms/{room_id}/end")
async def end_room(room_id: str):
    """End a classroom session and generate insights."""
    state = get_room_state(room_id)
    state["session_active"] = False
    result = await generate_insights(state)
    room = registry.get_room(room_id)
    if room:
        await room.broadcast({"type": "SESSION_ENDED", "insights": result})
    return result


@app.get("/api/rooms/{room_id}/insights")
async def get_insights(room_id: str):
    """Get post-class insights for a room."""
    state = get_room_state(room_id)
    if state.get("session_active", True):
        return {"error": "Session still active. End the session first."}
    result = await generate_insights(state)
    return result


@app.get("/api/rooms/{room_id}/state")
async def get_room_state_api(room_id: str):
    """Get the current classroom state (for debugging/demo)."""
    state = get_room_state(room_id)
    return {
        "floor_state": state.get("floor_state"),
        "lesson_context": state.get("lesson_context"),
        "student_profiles": state.get("student_profiles"),
        "common_gaps": state.get("common_gaps"),
        "agent_log": state.get("agent_log", [])[-10:],
        "language": state.get("language"),
        "ai_muted": state.get("ai_muted"),
        "transcript_length": len(state.get("transcript", [])),
    }


# ─── WebSocket Endpoint ────────────────────────────────────────────

@app.websocket("/ws/classroom/{room_id}")
async def classroom_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()
    room = registry.get_or_create(room_id)
    state = get_room_state(room_id)

    participant: Participant | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            # ─── JOIN ───────────────────────────────────────────
            if msg_type == "JOIN":
                user_id = msg.get("user_id", str(uuid.uuid4())[:8])
                name = msg.get("name", "Anonymous")
                role = msg.get("role", "student")

                participant = Participant(
                    websocket=websocket,
                    user_id=user_id,
                    name=name,
                    role=role,
                )
                room.participants[user_id] = participant

                await websocket.send_json({
                    "type": "JOINED",
                    "room_id": room_id,
                    "user_id": user_id,
                    "participants": [p for p in room.summary()["participants"]],
                })
                await room.broadcast({
                    "type": "PARTICIPANT_JOINED",
                    "name": name,
                    "role": role,
                    "participants": room.summary()["participants"],
                }, exclude_id=user_id)
                logger.info("User %s (%s) joined room %s", name, role, room_id)

            # ─── UTTERANCE ──────────────────────────────────────
            elif msg_type == "UTTERANCE":
                if not participant:
                    continue

                utterance = {
                    "speaker_id": participant.user_id,
                    "name": participant.name,
                    "role": participant.role,
                    "text": msg.get("text", ""),
                    "timestamp": datetime.now().isoformat(),
                    "is_final": msg.get("is_final", True),
                }

                # Broadcast utterance to all participants
                await room.broadcast({"type": "UTTERANCE", **utterance})

                # Only process final utterances through the orchestrator
                if utterance["is_final"] and utterance["text"].strip():
                    state["last_utterance"] = utterance

                    # If AI is muted, still update transcript but don't act
                    if state.get("ai_muted", False):
                        transcript = state.get("transcript", [])
                        transcript.append(utterance)
                        state["transcript"] = transcript[-50:]
                        continue

                    # Run the full agent pipeline
                    state = await process_utterance(state)

                    # Send floor state update
                    await room.broadcast({
                        "type": "FLOOR_STATE",
                        "state": state.get("floor_state", "OPEN_FLOOR"),
                        "badge": state.get("floor_badge", "⬜ Open floor"),
                        "ai_permitted": state.get("ai_permitted", False),
                    })

                    # Send agent log updates
                    recent_log = state.get("agent_log", [])[-5:]
                    if recent_log:
                        await room.broadcast({"type": "AGENT_LOG", "agents": recent_log})

                    # Send gap alert if detected
                    gap_alert = state.get("gap_alert")
                    if gap_alert:
                        await room.broadcast({
                            "type": "GAP_ALERT",
                            "concept": gap_alert.get("concept", ""),
                            "students": gap_alert.get("students", []),
                            "count": gap_alert.get("count", 0),
                            "severity": gap_alert.get("severity", 1),
                        })

                    # Execute pending action
                    action = state.get("pending_action")
                    if action:
                        action_type = action.get("type", "")
                        content = action.get("content", "")

                        if action_type == "WHISPER_EXPLAIN":
                            target = action.get("target_student_id", "")
                            logger.info("WHISPER to %s: %s", target, content[:80])
                            await room.whisper(target, {
                                "type": "WHISPER",
                                "content": content,
                                "concept": action.get("concept", ""),
                                "name": "Sahayak AI",
                            })
                            # Also broadcast a subtle notification to teacher
                            await room.broadcast({
                                "type": "WHISPER_NOTIFY",
                                "target_student_id": target,
                                "concept": action.get("concept", ""),
                            })
                        elif action_type == "EXPLAIN":
                            await room.broadcast({
                                "type": "AI_SPEAK",
                                "content": content,
                                "concept": action.get("concept", ""),
                            })
                        elif action_type == "QUIZ_ASK":
                            target = action.get("target_student_id", "")
                            await room.broadcast({
                                "type": "QUIZ_ASK",
                                "content": content,
                                "target_student_id": target,
                                "target_name": state.get("student_profiles", {}).get(target, {}).get("name", "student"),
                            })
                        elif action_type == "QUIZ_EVALUATE":
                            await room.broadcast({
                                "type": "QUIZ_RESULT",
                                "content": content,
                                "score": action.get("score", 50),
                                "correct": action.get("correct", ""),
                            })

                        # Reset floor after AI speaks
                        state["floor_state"] = "OPEN_FLOOR"
                        state["pending_action"] = None

            # ─── TEACHER CONTROL ────────────────────────────────
            elif msg_type == "TEACHER_CONTROL":
                if not participant or participant.role != "teacher":
                    continue

                control = msg.get("action", "")

                if control == "mute":
                    state["ai_muted"] = True
                    await room.broadcast({"type": "AI_MUTED", "muted": True})
                    logger.info("AI muted in room %s", room_id)

                elif control == "unmute":
                    state["ai_muted"] = False
                    await room.broadcast({"type": "AI_MUTED", "muted": False})
                    logger.info("AI unmuted in room %s", room_id)

                elif control == "quiz":
                    target = msg.get("target_student_id", "")
                    if target:
                        state["quiz_request"] = target
                        logger.info("Quiz requested for %s in room %s", target, room_id)

                elif control == "end_class":
                    state["session_active"] = False
                    result = await generate_insights(state)
                    await room.broadcast({
                        "type": "SESSION_ENDED",
                        "insights": result,
                    })
                    logger.info("Class ended in room %s", room_id)

                elif control == "approve":
                    action_id = msg.get("action_id", "")
                    # In approve mode, teacher approves a pending action
                    # For now, auto-execute is default
                    pass

                elif control == "approve_mode":
                    state["approve_mode"] = msg.get("enabled", False)
                    await room.broadcast({
                        "type": "APPROVE_MODE",
                        "enabled": state["approve_mode"],
                    })

            # ─── QUIZ ANSWER ────────────────────────────────────
            elif msg_type == "QUIZ_ANSWER":
                if not participant:
                    continue

                if state.get("quiz_active") and state.get("quiz_target_student") == participant.user_id:
                    state["quiz_answer_pending"] = {
                        "question": state.get("quiz_question", ""),
                        "expected_answer": state.get("quiz_answer", ""),
                        "student_answer": msg.get("answer", ""),
                        "student_name": participant.name,
                    }
                    # Process through orchestrator
                    state["last_utterance"] = {
                        "speaker_id": participant.user_id,
                        "name": participant.name,
                        "role": "student",
                        "text": msg.get("answer", ""),
                        "is_final": True,
                    }
                    if not state.get("ai_muted", False):
                        state = await process_utterance(state)
                        action = state.get("pending_action")
                        if action and action.get("type") == "QUIZ_EVALUATE":
                            await room.broadcast({
                                "type": "QUIZ_RESULT",
                                "content": action.get("content", ""),
                                "score": action.get("score", 50),
                                "correct": action.get("correct", ""),
                            })
                            state["floor_state"] = "OPEN_FLOOR"
                            state["pending_action"] = None

            # ─── PING ───────────────────────────────────────────
            elif msg_type == "PING":
                await websocket.send_json({"type": "PONG"})

    except WebSocketDisconnect:
        if participant:
            room.participants.pop(participant.user_id, None)
            await room.broadcast({
                "type": "PARTICIPANT_LEFT",
                "name": participant.name,
                "role": participant.role,
                "participants": room.summary()["participants"],
            })
            logger.info("User %s left room %s", participant.name, room_id)
            if not room.participants:
                registry.remove_room(room_id)
                room_states.pop(room_id, None)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        if participant:
            room.participants.pop(participant.user_id, None)
