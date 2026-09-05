"""
Server-side voice broadcast: pipes Sahayak's Piper speech into the room's
Agora channel via the `agora_voice_bridge` subprocess (which runs inside the
Piper venv where the Agora Python SDK has wheels).
"""

import json
import logging
import os
import subprocess
import threading
import time

from agora_token_builder import RtcTokenBuilder

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(BACKEND_DIR))

AGORA_APP_ID = os.getenv("AGORA_APP_ID", "")
AGORA_APP_CERTIFICATE = os.getenv("AGORA_APP_CERTIFICATE", "")
# The AI's uid in every channel. Numeric and > 1e9 so it can never collide with
# client uids (frontend uses char-code sums mod 1e9). 0x53414841 = "SAHA".
AI_UID = int(os.getenv("AGORA_AI_UID", "1396787265"))
TOKEN_TTL_S = 3600

BRIDGE_SCRIPT = os.path.join(PROJECT_DIR, "scripts", "agora_voice_bridge.py")
BRIDGE_PYTHON = os.getenv(
    "PIPER_BIN",
    os.path.join(PROJECT_DIR, "piper-venv", "bin", "piper"),
).replace("/bin/piper", "/bin/python3")

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_proc: subprocess.Popen | None = None
_id_counter = 0


def available() -> bool:
    return bool(AGORA_APP_ID and AGORA_APP_CERTIFICATE) and os.path.exists(BRIDGE_SCRIPT)


def _start() -> bool:
    """Start the bridge subprocess if not already running."""
    global _proc
    with _lock:
        if _proc and _proc.poll() is None:
            return True
        env = dict(os.environ)
        try:
            _proc = subprocess.Popen(
                [BRIDGE_PYTHON, BRIDGE_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
            )
            return True
        except FileNotFoundError as e:
            logger.error("cannot start voice bridge (%s)", e)
            _proc = None
            return False


def _respond(cmd_id: str, timeout_ms: int = 60000):
    global _proc
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        line = _proc.stdout.readline()
        if not line:
            return None
        try:
            resp = json.loads(line)
        except json.JSONDecodeError:
            continue
        if resp.get("id") == cmd_id:
            return resp
    return None


def _command(cmd: dict, timeout_ms: int = 60000) -> dict:
    global _id_counter, _proc
    if not _start():
        return {"ok": False, "error": "bridge unavailable"}
    with _lock:
        _id_counter += 1
        cmd_id = f"{_id_counter}"
        payload = {"id": cmd_id, **cmd}
        try:
            _proc.stdin.write(json.dumps(payload) + "\n")
            _proc.stdin.flush()
        except ValueError as e:
            _proc = None
            return {"ok": False, "error": f"bridge not running: {e}"}
    resp = _respond(cmd_id, timeout_ms)
    if resp is None:
        return {"ok": False, "error": "bridge timeout"}
    return resp


def mint_channel_token(channel: str) -> str:
    """Return a publisher token for the AI's uid in this channel."""
    expire_ts = int(time.time()) + TOKEN_TTL_S
    return RtcTokenBuilder.buildTokenWithUid(
        AGORA_APP_ID, AGORA_APP_CERTIFICATE, channel, AI_UID, 1, expire_ts
    )


def broadcast_speech(channel: str, text: str, lang: str = "en") -> bool:
    """Synthesize and push `text` into the channel in the background. Returns True if initiated."""
    if not available():
        return False
    try:
        token = mint_channel_token(channel)
    except Exception as e:  # noqa: BLE001
        logger.error("token mint failed: %s", e)
        return False

    def worker():
        try:
            resp = _command({"cmd": "speak", "channel": channel, "token": token, "text": text, "lang": lang})
            logger.info("voice broadcast → %s (lang=%s): %s", channel, lang, resp)
        except Exception as e:  # noqa: BLE001
            logger.error("voice broadcast failed for %s: %s", channel, e)

    threading.Thread(target=worker, daemon=True, name="ai-voice").start()
    return True


def shutdown():
    global _proc
    with _lock:
        if _proc and _proc.poll() is None:
            try:
                _proc.stdin.write(json.dumps({"cmd": "shutdown", "id": "bye"}) + "\n")
                _proc.stdin.flush()
            except Exception:  # noqa: BLE001
                pass
            try:
                _proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                _proc.kill()
        _proc = None