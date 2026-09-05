"""
Human-like text-to-speech for Sahayak Live.

Uses a local neural TTS engine (Piper) for genuinely natural voices, and
falls back to the macOS `say` synthesizer if Piper is not set up.

Also humanizes the raw LLM text so the spoken output sounds conversational
rather than robotic (expands symbols/abbreviations, adds natural pauses,
softens markup).
"""

import os
import json
import re
import shutil
import subprocess
import tempfile
import time

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


# ─── Multilingual voices (10+ Indian languages) ────────────────────
# Piper runs fully offline but only ships a handful of Indian voices.
# For every other Indian language we fall back to Microsoft edge-tts
# (online). Language is auto-detected from the message text.

# Piper voices bundled by scripts/setup_piper.sh (offline): en, hi, te,
# ml, mr. Add more by dropping the .onnx/.json into piper-venv/voices and
# extending this map.
PIPER_LANG_VOICES = {
    "en": "en_US-amy-medium",
    "hi": "hi_IN-pratham-medium",
    "te": "te_IN-maya-medium",
    "ml": "ml_IN-meera-medium",
    "mr": "mr_IN-google-medium",
}

# Unicode block ranges for Indian scripts -> ISO-639-1 code
_SCRIPT_LANGS = [
    (0x0900, 0x097F, "hi"),  # Devanagari (Hindi, Marathi)
    (0x0980, 0x09FF, "bn"),  # Bengali
    (0x0A00, 0x0A7F, "pa"),  # Gurmukhi (Punjabi)
    (0x0A80, 0x0AFF, "gu"),  # Gujarati
    (0x0B00, 0x0B7F, "or"),  # Odia
    (0x0B80, 0x0BFF, "ta"),  # Tamil
    (0x0C00, 0x0C7F, "te"),  # Telugu
    (0x0C80, 0x0CFF, "kn"),  # Kannada
    (0x0D00, 0x0D7F, "ml"),  # Malayalam
    (0x0600, 0x06FF, "ur"),  # Arabic (Urdu)
]

# Small Hinglish lexicon to catch romanized Hindi
_HINGLISH_HINTS = re.compile(
    r"\b(?:hai|hain|nahi|kyu|kyun|kya|mera|meri|tum|aap|bhai|samajh|"
    r"padh|padhai|bahut|acha|accha|thik|theek|puch|bolo|bolna|kal|"
    r"aaj|yaha|sir|madam)\b",
    re.IGNORECASE,
)

# Marathi-only Devanagari sign + words to disambiguate from Hindi.
# NOTE: no \b boundaries — Devanagari words often end in combining vowel
# marks (Mn category) which are not word characters, so \b can't match.
_MR_HINTS = re.compile(r"[ळऴ]|वरय|आम्ही|आहे|नाही")


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


# ─── Language detection ────────────────────────────────────────────

def detect_language(text: str) -> str:
    """Heuristic language detection for Indian classroom messages.

    Returns an ISO-639-1 code (en, hi, bn, pa, gu, or, ta, te, kn, ml, mr,
    ur). Prefers the native Indic script; falls back to a small Hinglish
    lexicon for romanized Hindi.
    """
    if not text or not text.strip():
        return "en"
    t = text.strip()
    counts: dict[str, int] = {}
    for cp in t:
        for lo, hi, lang in _SCRIPT_LANGS:
            if lo <= ord(cp) <= hi:
                counts[lang] = counts.get(lang, 0) + 1
                break
    if counts:
        lang = max(counts, key=counts.get)
        if lang == "hi" and _MR_HINTS.search(t):
            return "mr"
        return lang
    if len(_HINGLISH_HINTS.findall(t)) >= 2:
        return "hi"
    return "en"


# ─── Edge-tts (online fallback for every Indian language) ──────────

_EDGE_VOICES: dict[str, list[tuple[int, str]]] = {}
_EDGE_VOICES_AT = 0.0
EDGE_VOICES_TTL = 3600.0


def _edge_available() -> bool:
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return _piper_venv_python() is not None or False


_LIST_SUB_SNIPPET = (
    "import asyncio,json,sys\n"
    "async def _r():\n"
    " import edge_tts\n"
    " vs=await edge_tts.list_voices()\n"
    " sys.stdout.write(json.dumps([{'Locale':v.get('Locale'),'ShortName':v.get('ShortName'),"
    "'Gender':v.get('Gender')} for v in vs]))\n"
    "asyncio.run(_r())\n"
)


def _list_voices_subproc() -> list[dict]:
    """List edge-tts voices by running the Piper venv when this interpreter lacks edge_tts."""
    py = _piper_venv_python()
    if not py or not os.path.exists(py):
        return []
    try:
        r = subprocess.run([py, "-c", _LIST_SUB_SNIPPET], capture_output=True, timeout=60, check=True)
        data = json.loads(r.stdout)
        return data if isinstance(data, list) else []
    except Exception:  # noqa: BLE001
        return []


def _load_edge_voices() -> dict[str, list[tuple[int, str]]]:
    """Cache a language-code -> ranked voice list from edge-tts's registry.

    Ranking scores: prefer the `*-IN` (India) locale, then female voices,
    then male. edge-tts covers hi, bn, ta, te, ml, mr, gu, kn, ur (and en).
    """
    global _EDGE_VOICES, _EDGE_VOICES_AT
    now = time.time()
    if _EDGE_VOICES and now - _EDGE_VOICES_AT < EDGE_VOICES_TTL:
        return _EDGE_VOICES
    if not _edge_available():
        return {}

    try:
        import asyncio
        import edge_tts

        async def _list():
            return await edge_tts.list_voices()

        voices = asyncio.run(_list())
    except ImportError:
        voices = _list_voices_subproc()
    except Exception:  # noqa: BLE001
        voices = []
    if not voices:
        _EDGE_VOICES = _EDGE_VOICES or {}
        _EDGE_VOICES_AT = now
        return _EDGE_VOICES

    by_code: dict[str, list[tuple[int, str]]] = {}
    for v in voices:
        locale = str(v.get("Locale") or "").lower()
        parts = locale.split("-")
        region = parts[-1] if len(parts) > 1 else ""
        code = parts[0]
        if not code:
            continue
        short = v.get("ShortName") or ""
        if not short:
            continue
        gender = str(v.get("Gender") or "").lower()
        score = 0
        if region == "in":
            score -= 4  # prefer India locale
        if gender == "female":
            score -= 2
        elif gender == "male":
            score -= 1
        by_code.setdefault(code, []).append((score, short))
    _EDGE_VOICES = {code: sorted(lst) for code, lst in by_code.items()}
    _EDGE_VOICES_AT = now
    return _EDGE_VOICES


def _edge_voice(lang: str) -> str | None:
    lst = _load_edge_voices().get(lang)
    return lst[0][1] if lst else None


# edge-tts uses an event loop + aiohttp and is only guaranteed available in
# the Piper venv (main backend runs system Python). If it's not importable in
# this interpreter, fall back to running edge-tts in the Piper venv.
_EDGE_SUB_SNIPPET = r"""
import asyncio, os, shutil, subprocess, sys
text, voice, wav_out = sys.argv[1], sys.argv[2], sys.argv[3]
mp3 = wav_out + ".mp3"
async def _run():
    import edge_tts
    await edge_tts.Communicate(text, voice, rate="+0%").save(mp3)
asyncio.run(_run())
if not os.path.exists(mp3) or os.path.getsize(mp3) < 100:
    sys.exit(2)
ffmpeg = shutil.which("ffmpeg")
if ffmpeg:
    subprocess.run([ffmpeg, "-y", "-v", "error", "-i", mp3,
                    "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1", wav_out],
                   check=True)
else:
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", "-c", "1", mp3, wav_out],
                   check=True)
"""


def _piper_venv_python() -> str | None:
    if PIPER_BIN and PIPER_BIN.endswith("piper"):
        return PIPER_BIN.rsplit("/bin/piper", 1)[0] + "/bin/python3"
    return None


def _edge_synthesize_inproc(text: str, voice: str) -> bytes:
    """Synthesize via Microsoft edge-tts (in-process) and decode MP3 -> WAV."""
    import asyncio
    import edge_tts
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as t:
        mp3_path = t.name
    wav_path = mp3_path[:-4] + ".wav"
    try:
        async def _run():
            communicate = edge_tts.Communicate(text, voice, rate="+0%")
            await communicate.save(mp3_path)
        asyncio.run(_run())
        if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) < 100:
            return b""
        # Decode mp3 -> wav (ffmpeg preferred, macOS afconvert fallback)
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", mp3_path,
                 "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1", wav_path],
                check=True, capture_output=True, timeout=60,
            )
        except Exception:  # noqa: BLE001
            subprocess.run(
                ["afconvert", "-f", "WAVE", "-d", "LEI16", "-c", "1", mp3_path, wav_path],
                check=True, capture_output=True, timeout=60,
            )
        with open(wav_path, "rb") as f:
            return f.read()
    finally:
        for p in (mp3_path, wav_path):
            try:
                os.remove(p)
            except OSError:
                pass


def _edge_synthesize_subproc(text: str, voice: str) -> bytes:
    """Run edge-tts in the Piper venv when this interpreter lacks it."""
    py = _piper_venv_python()
    if not py or not os.path.exists(py):
        raise RuntimeError("edge-tts unavailable and piper venv missing")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as t:
        wav_out = t.name
    try:
        subprocess.run(
            [py, "-c", _EDGE_SUB_SNIPPET, text, voice, wav_out],
            check=True, capture_output=True, timeout=90,
        )
        with open(wav_out, "rb") as f:
            return f.read()
    finally:
        for p in (wav_out, wav_out + ".mp3"):
            try:
                os.remove(p)
            except OSError:
                pass


def _edge_synthesize(text: str, voice: str) -> bytes:
    try:
        return _edge_synthesize_inproc(text, voice)
    except ImportError:
        return _edge_synthesize_subproc(text, voice)


# ─── Synthesis (multi-language) ────────────────────────────────────

def _piper_model(lang: str) -> str | None:
    """Return the piper model file for `lang` if it is installed."""
    name = PIPER_LANG_VOICES.get(lang, PIPER_MODEL)
    return name if os.path.exists(os.path.join(PIPER_VOICE_DIR, name + ".onnx")) else None


def synthesize(text: str, lang: str | None = None) -> tuple[bytes, str]:
    """Synthesize speech for `text`. Returns (wav_bytes, media_type).

    `lang` (ISO-639-1, e.g. "hi") is an optional hint; when omitted the
    language is auto-detected from the text. Resolution order: Piper
    (offline) -> edge-tts (online) -> macOS `say`.
    """
    spoken = humanize(text)
    if lang and "-" in lang:
        lang = lang.split("-")[0]
    if not lang:
        lang = detect_language(spoken)

    if _piper_available():
        model = _piper_model(lang)
        if model:
            try:
                wav = _piper_synthesize(spoken, model)
                if wav:
                    return wav, "audio/wav"
            except Exception as e:  # noqa: BLE001
                print(f"[tts] Piper failed, falling back: {e}")

    voice = _edge_voice(lang)
    if voice:
        try:
            wav = _edge_synthesize(spoken, voice)
            if wav:
                return wav, "audio/wav"
        except Exception as e:  # noqa: BLE001
            print(f"[tts] edge-tts failed, falling back to say: {e}")

    return _say_synthesize(spoken), "audio/wav"


def _piper_synthesize(text: str, model: str | None = None) -> bytes:
    model_path = os.path.join(PIPER_VOICE_DIR, model or PIPER_MODEL)
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
