"""
Sahayak Live — Room Registry
In-memory room manager for WebSocket connections.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class Participant:
    websocket: WebSocket
    user_id: str
    name: str
    role: str
    is_muted: bool = False


@dataclass
class Room:
    room_id: str
    participants: dict[str, Participant] = field(default_factory=dict)
    transcript: list[dict] = field(default_factory=list)
    floor_state: str = "OPEN_FLOOR"
    ai_muted: bool = False
    session_active: bool = True
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def get_teacher(self) -> Participant | None:
        for p in self.participants.values():
            if p.role == "teacher":
                return p
        return None

    def get_student(self, user_id: str) -> Participant | None:
        return self.participants.get(user_id)

    async def broadcast(self, message: dict, exclude_id: str | None = None):
        """Send a message to all participants (optionally excluding one)."""
        dead = []
        for uid, p in self.participants.items():
            if exclude_id and uid == exclude_id:
                continue
            try:
                await p.websocket.send_json(message)
            except Exception:
                dead.append(uid)
        for uid in dead:
            self.participants.pop(uid, None)

    async def whisper(self, target_user_id: str, message: dict):
        """Send a message to a single participant."""
        p = self.participants.get(target_user_id)
        if p:
            try:
                await p.websocket.send_json(message)
            except Exception:
                self.participants.pop(target_user_id, None)

    def summary(self) -> dict:
        return {
            "room_id": self.room_id,
            "participant_count": len(self.participants),
            "participants": [
                {"user_id": p.user_id, "name": p.name, "role": p.role}
                for p in self.participants.values()
            ],
            "floor_state": self.floor_state,
            "ai_muted": self.ai_muted,
            "session_active": self.session_active,
            "transcript_length": len(self.transcript),
        }


class RoomRegistry:
    """Global in-memory registry of active rooms."""

    def __init__(self):
        self.rooms: dict[str, Room] = {}

    def create_room(self, room_id: str) -> Room:
        room = Room(room_id=room_id)
        self.rooms[room_id] = room
        logger.info("Room created: %s", room_id)
        return room

    def get_or_create(self, room_id: str) -> Room:
        if room_id not in self.rooms:
            return self.create_room(room_id)
        return self.rooms[room_id]

    def get_room(self, room_id: str) -> Room | None:
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str):
        self.rooms.pop(room_id, None)
        logger.info("Room removed: %s", room_id)

    def list_rooms(self) -> list[dict]:
        return [r.summary() for r in self.rooms.values()]


registry = RoomRegistry()
