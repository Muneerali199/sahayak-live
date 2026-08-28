"""
Sahayak Live — Classroom State
Shared state for the multi-agent LangGraph orchestrator.
"""

from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


FloorState = Literal["TEACHER_TALKING", "STUDENT_TALKING", "OPEN_FLOOR", "AI_SPEAKING"]
Role = Literal["teacher", "student", "ai"]
StudentLevel = Literal["beginner", "intermediate", "advanced"]
ActionType = Literal["EXPLAIN", "WHISPER_EXPLAIN", "QUIZ_ASK", "QUIZ_EVALUATE", "ANSWER_CONTEXTUAL", "NONE"]


class Utterance(BaseModel):
    speaker_id: str
    name: str
    role: Role
    text: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    is_final: bool = True


class StudentProfile(BaseModel):
    student_id: str
    name: str
    level: StudentLevel = "intermediate"
    gaps: list[str] = Field(default_factory=list)
    comprehension_score: float = 0.5
    utterance_count: int = 0
    confusion_signals: int = 0


class GapCluster(BaseModel):
    concept: str
    struggling_students: list[str] = Field(default_factory=list)
    severity: int = 1
    first_detected: str = Field(default_factory=lambda: datetime.now().isoformat())


class PendingAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: ActionType
    target_student_id: str | None = None
    concept: str = ""
    draft_content: str = ""
    reasoning: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    approved: bool = False


class AgentLog(BaseModel):
    agent: str
    action: str
    status: str = "done"
    detail: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ClassroomState(TypedDict, total=False):
    room_id: str
    transcript: list[dict]
    floor_state: str
    floor_badge: str
    current_speaker_id: str
    current_speaker_role: str
    lesson_context: str
    lesson_topic: str
    student_profiles: dict[str, dict]
    common_gaps: list[dict]
    pending_actions: list[dict]
    pending_action: dict
    last_action: str
    ai_muted: bool
    ai_permitted: bool
    session_active: bool
    agent_log: list[dict]
    last_utterance: dict
    language: str
    quiz_active: bool
    quiz_target_student: str
    quiz_question: str
    quiz_answer: str
    quiz_request: str
    quiz_answer_pending: dict
    gap_alert: dict
    addressed_whispers: list[str]
    approve_mode: bool
