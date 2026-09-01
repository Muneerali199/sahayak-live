"use client";

// TTS manager that prefers backend-generated audio (plays via <audio>, guaranteed
// audible on any device) and falls back to the browser's built-in speechSynthesis.

let synthesis: SpeechSynthesis | null = null;
let audioEl: HTMLAudioElement | null = null;
let backendAvailable: boolean | null = null; // lazily probed

if (typeof window !== "undefined" && "speechSynthesis" in window) {
  synthesis = window.speechSynthesis;
}

// Prefer the Indian English browser voice when available
function pickBrowserVoice() {
  if (!synthesis) return null;
  const voices = synthesis.getVoices();
  return (
    voices.find((v) => v.lang.startsWith("en-IN")) ||
    voices.find((v) => v.lang.startsWith("en")) ||
    voices[0] ||
    null
  );
}
if (synthesis) {
  pickBrowserVoice();
  synthesis.onvoiceschanged = pickBrowserVoice;
}

async function probeBackend(): Promise<boolean> {
  if (backendAvailable !== null) return backendAvailable;
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 2500);
    const r = await fetch(
      `http://127.0.0.1:8001/api/health`,
      { signal: ctrl.signal }
    );
    clearTimeout(t);
    backendAvailable = r.ok;
  } catch {
    backendAvailable = false;
  }
  return backendAvailable;
}

function playAudio(src: string, onError: () => void) {
  if (!audioEl) {
    audioEl = new Audio();
  }
  audioEl.pause();
  audioEl.src = src;
  audioEl.playbackRate = 1;
  audioEl.onerror = () => onError();
  audioEl.play().catch(onError);
}

export function speak(text: string, lang: string = "en-IN") {
  if (!text) return;

  // Prefer backend TTS (guaranteed audible, uses local Indian voice)
  probeBackend().then((ok) => {
    if (ok) {
      playAudio(
        `http://127.0.0.1:8001/api/tts?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(lang)}`,
        () => playBrowserSpeech(text, lang)
      );
      return;
    }
    playBrowserSpeech(text, lang);
  });
}

function playBrowserSpeech(text: string, lang: string) {
  if (!synthesis) return;
  synthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = pickBrowserVoice();
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  utterance.lang = lang;
  synthesis.speak(utterance);
}

export function stopSpeaking() {
  if (audioEl) {
    audioEl.pause();
    audioEl.src = "";
  }
  if (synthesis) synthesis.cancel();
}

export function isSpeaking() {
  const a = audioEl ? !audioEl.paused && !audioEl.ended : false;
  return a || (synthesis?.speaking ?? false);
}
