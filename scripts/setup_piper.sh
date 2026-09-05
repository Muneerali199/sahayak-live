#!/usr/bin/env bash
# Setup local neural TTS (Piper) for Sahayak Live.
# Creates a Python 3.11 venv (onnxruntime needs < Python 3.14) and downloads
# a natural "Amy" voice model. No API key required; runs fully offline.
#
# Usage:
#   bash scripts/setup_piper.sh
#
# Requires: an available python3.11 (or set PYTHON below).

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/piper-venv"
VOICE_DIR="$VENV_DIR/voices"
MODEL="en_US-amy-medium.onnx"

# Indian-language Piper voices (offline). edge-tts covers the rest online.
INDIAN_VOICES="hi_IN-pratham-medium te_IN-maya-medium ml_IN-meera-medium mr_IN-google-medium"

# Pick a python3.11 binary
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for c in python3.11 python3.12; do
    if command -v "$c" >/dev/null 2>&1; then PYTHON="$(command -v "$c")"; break; fi
  done
fi
if [ -z "$PYTHON" ]; then
  echo "ERROR: python3.11 or python3.12 not found. Install one first." >&2
  exit 1
fi
echo "Using Python: $PYTHON"

mkdir -p "$VOICE_DIR"

if [ ! -x "$VENV_DIR/bin/piper" ]; then
  echo "Creating venv at $VENV_DIR ..."
  "$PYTHON" -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --upgrade pip
  "$VENV_DIR/bin/pip" install "piper-tts==1.3.0"
  # Microsoft edge-tts = online voices for Indian languages not in Piper
  "$VENV_DIR/bin/pip" install "edge-tts>=7.0.0"
else
  echo "venv already present at $VENV_DIR"
  "$VENV_DIR/bin/pip" install -q "edge-tts>=7.0.0" || true
fi

if [ ! -f "$VOICE_DIR/$MODEL" ]; then
  echo "Downloading voice model $MODEL (~63MB) ..."
  curl -sL -o "$VOICE_DIR/$MODEL" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/$MODEL"
  curl -sL -o "$VOICE_DIR/$MODEL.json" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/$MODEL.json"
else
  echo "Voice model already present"
fi

for MODEL in $INDIAN_VOICES; do
  if [ ! -s "$VOICE_DIR/$MODEL.onnx" ]; then
    lang_dir=$(case "$MODEL" in hi_IN*) echo "hi/hi_IN";; te_IN*) echo "te/te_IN";; ml_IN*) echo "ml/ml_IN";; mr_IN*) echo "mr/mr_IN";; esac)
    QUALITY=medium
    echo "Downloading Indian voice $MODEL (~64MB) ..."
    curl -sL -o "$VOICE_DIR/$MODEL.onnx" \
      "https://huggingface.co/rhasspy/piper-voices/resolve/main/$lang_dir/$QUALITY/$MODEL.onnx" &&
    curl -sL -o "$VOICE_DIR/$MODEL.onnx.json" \
      "https://huggingface.co/rhasspy/piper-voices/resolve/main/$lang_dir/$QUALITY/$MODEL.onnx.json"
  fi
done

echo
echo "Piper TTS is ready!"
echo "TTS engine auto-detected by the backend (x-tts-engine: piper)."
