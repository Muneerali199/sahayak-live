"use client";

let synthesis: SpeechSynthesis | null = null;
let currentVoice: SpeechSynthesisVoice | null = null;

if (typeof window !== "undefined" && "speechSynthesis" in window) {
  synthesis = window.speechSynthesis;
  const loadVoices = () => {
    const voices = synthesis!.getVoices();
    // Prefer natural English voices, then any English, then first available
    currentVoice =
      voices.find((v) => v.lang.startsWith("en") && v.name.includes("Natural")) ||
      voices.find((v) => v.lang.startsWith("en") && v.name.includes("Google")) ||
      voices.find((v) => v.lang.startsWith("en")) ||
      voices[0] ||
      null;
  };
  loadVoices();
  synthesis.onvoiceschanged = loadVoices;
}

export function speak(text: string, lang: string = "en-US") {
  if (!synthesis || !text) return;
  synthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.voice = currentVoice;
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;
  utterance.lang = lang;
  synthesis.speak(utterance);
}

export function stopSpeaking() {
  if (synthesis) synthesis.cancel();
}

export function isSpeaking() {
  return synthesis?.speaking ?? false;
}
