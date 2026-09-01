"""
Human-like text-to-speech for Sahayak Live.

Uses a local neural TTS engine (Piper) for genuinely natural voices, and
falls back to the macOS `say` synthesizer if Piper is not set up.

Also humanizes the raw LLM text so the spoken output sounds conversational
rather than robotic (expands symbols/abbreviations, adds natural pauses,
softens markup).
"""

import os
import re
import shutil
import subprocess
import tempfile

# ─── Piper configuration ───────────────────────────────────────────

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PIPER_BIN = os.getenv(
    "PIPER_BIN",
    os.path.join(PROJECT_DIR, "piper-venv", "bin", "piper"),
)
PIPER_VOICE_DIR = os.getenv(
    "PIPER_VOICE_DIR",
    os.path.join(PROJECT_DIR, "piper-venv", "voices"),
)
PIPER_MODEL = os.getenv("PIPER_MODEL", "en_US-amy-medium.onnx")
PIPER_LENGTH_SCALE = float(os.getenv("PIPER_LENGTH_SCALE", "1.1"))  # slightly slower=calmer
PIPER_NOISE_SCALE = float(os.getenv("PIPER_NOISE_SCALE", "0.667"))
PIPER_NOISE_W = float(os.getenv("PIPER_NOISE_W", "0.8"))
PIPER_SENTENCE_SILENCE = float(os.getenv("PIPER_SENTENCE_SILENCE", "0.15"))

FALLBACK_VOICE = os.getenv("TTS_VOICE", "Rishi")  # macOS say fallback voice


def _piper_available() -> bool:
    """Return True if the Piper binary and voice model are present."""
    model_path = os.path.join(PIPER_VOICE_DIR, PIPER_MODEL)
    return (
        shutil.which(PIPER_BIN) or os.path.exists(PIPER_BIN)
    ) and os.path.exists(model_path)


# ─── Text humanization ─────────────────────────────────────────────

_NUM_WORDS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
    "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen",
    "14": "fourteen", "15": "fifteen", "16": "sixteen", "17": "seventeen",
    "18": "eighteen", "19": "nineteen", "20": "twenty", "30": "thirty",
    "40": "forty", "50": "fifty", "60": "sixty", "70": "seventy",
    "80": "eighty", "90": "ninety",
}


def _fraction_to_words(match) -> str:
    """Convert a fraction like 1/4 or 3 1/2 into spoken words."""
    body = match.group(0)
    # Whole + fraction e.g. "3 1/2"
    ws = re.match(r"\s*\d+\s+", body)
    whole = ""
    if ws and re.match(r"\d+\s+\d+/\d+", body):
        whole_first = re.match(r"\s*(\d+)\s+(?=\d+/\d+)", body)
        if whole_first:
            whole = whole_first.group(1)
            body = body[whole_first.end():]
        else:
            whole = ""

    frac = re.search(r"(\d+)/(\d+)", body)
    if not frac:
        return body
    num, den = frac.group(1), frac.group(2)
    spoken = f"{_NUM_WORDS.get(num, num)} over {_NUM_WORDS.get(den, den)}"
    if whole:
        spoken = f"{_NUM_WORDS.get(whole, whole)} and {spoken}"
    return spoken


# Common symbols/abbreviations -> spoken words
# NOTE: keys/values are applied as whole tokens at word boundaries
_SYMBOL_MAP = {
    "pi": "pi",
    "e.g.": "for example",
    "i.e.": "that is",
    "vs.": "versus",
    "approx.": "approximately",
    "etc.": "and so on",
    "kg": "kilograms",
    "km": "kilometers",
    "cm": "centimeters",
    "mm": "millimeters",
    "min": "minutes",
    "sec": "seconds",
    "hrs": "hours",
    "deg": "degrees",
}

_MD_CLEAN = re.compile(r"[*_`#>~]")


def humanize(text: str) -> str:
    """Turn raw model text into natural, speech-friendly prose."""
    if not text:
        return text

    t = text.strip()

    # Expand fractions first (so the slash isn't misread) — e.g. "1/4", "3 1/2"
    t = re.sub(r"\b\d+\s+\d+/\d+\b|\b\d+/\d+\b", _fraction_to_words, t)

    # Simplify remaining "a/b" (may be a ratio) -> "a over b"
    t = re.sub(r"\b(\d+)/(\d+)\b", _frac_pair, t)

    # Expand dollar/euro, percent, plus/minus, equals, multiplications
    t = re.sub(r"\$\s*(\d+)", r"\1 dollars", t)
    t = re.sub(r"€\s*(\d+)", r"\1 euros", t)
    t = re.sub(r"(\d+)\s*%", r"\1 percent", t)
    t = re.sub(r"(\d+)\s*(?:\+|plus)\s*(\d+)", r"\1 plus \2", t)
    t = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1 minus \2", t)
    t = re.sub(r"(\d+)\s*(?:×|\*|x)\s*(\d+)", r"\1 times \2", t)
    t = re.sub(r"(\d+)\s*(?:÷)\s*(\d+)", r"\1 divided by \2", t)
    t = re.sub(r"(\d+)\s*=\s*(\d+)", r"\1 equals \2", t)

    # Expand common abbreviations as whole tokens (word boundaries)
    pattern = re.compile(
        r"(?<![\w])(" + "|".join(re.escape(k) for k in sorted(_SYMBOL_MAP, key=len, reverse=True)) + r")(?![\w])",
        re.IGNORECASE,
    )
    for key, value in sorted(_SYMBOL_MAP.items(), key=lambda kv: -len(kv[0])):
        t = re.sub(
            r"(?<![\w])" + re.escape(key) + r"(?![\w])",
            value,
            t,
            flags=re.IGNORECASE,
        )

    # Strip markdown syntax that shouldn't be spoken
    t = _MD_CLEAN.sub("", t)

    # Collapse repeated whitespace
    t = re.sub(r"\s+", " ", t).strip()

    # Ensure it ends with punctuation so Piper adds natural final intonation
    if t and t[-1] not in ".!?":
        t += "."
    return t


def _frac_pair(match) -> str:
    a, b = match.group(1), match.group(2)
    return f"{_NUM_WORDS.get(a, a)} over {_NUM_WORDS.get(b, b)}"


# ─── Synthesis ─────────────────────────────────────────────────────

def synthesize(text: str) -> tuple[bytes, str]:
    """Synthesize speech. Returns (wav_bytes, media_type)."""
    spoken = humanize(text)

    if _piper_available():
        try:
            wav = _piper_synthesize(spoken)
            if wav:
                return wav, "audio/wav"
        except Exception as e:  # noqa: BLE001
            print(f"[tts] Piper failed, falling back to say: {e}")

    return _say_synthesize(spoken), "audio/wav"


def _piper_synthesize(text: str) -> bytes:
    model_path = os.path.join(PIPER_VOICE_DIR, PIPER_MODEL)
    config_path = model_path + ".json"
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = tmp.name
    try:
        cmd = [
            PIPER_BIN,
            "-m", model_path,
            "-c", config_path,
            "-f", out_path,
            "--length-scale", str(PIPER_LENGTH_SCALE),
            "--noise-scale", str(PIPER_NOISE_SCALE),
            "--noise-w", str(PIPER_NOISE_W),
            "--sentence-silence", str(PIPER_SENTENCE_SILENCE),
        ]
        subprocess.run(
            cmd, input=text.encode("utf-8"), check=True,
            capture_output=True, timeout=60,
        )
        with open(out_path, "rb") as f:
            data = f.read()
        return data
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass


def _say_synthesize(text: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_path = tmp.name
    try:
        subprocess.run(
            ["say", "-v", FALLBACK_VOICE, "-o", out_path,
             "--data-format=LEI16@22050", text],
            check=True, capture_output=True, timeout=30,
        )
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass
