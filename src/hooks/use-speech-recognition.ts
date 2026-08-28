"use client";

import { useEffect, useRef, useState, useCallback } from "react";

interface SpeechRecognitionHook {
  isListening: boolean;
  isSupported: boolean;
  error: string | null;
  start: () => void;
  stop: () => void;
  interimTranscript: string;
}

export function useSpeechRecognition(
  onFinalResult: (text: string) => void,
  lang: string = "en-US"
): SpeechRecognitionHook {
  const recognitionRef = useRef<any>(null);
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interimTranscript, setInterimTranscript] = useState("");
  const enabledRef = useRef(false);
  const onFinalRef = useRef(onFinalResult);
  onFinalRef.current = onFinalResult;

  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setIsSupported(false);
      return;
    }
    setIsSupported(true);

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = lang;

    recognition.onresult = (event: any) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          const text = transcript.trim();
          if (text) onFinalRef.current(text);
          setInterimTranscript("");
        } else {
          interim += transcript;
        }
      }
      if (interim) setInterimTranscript(interim);
    };

    recognition.onerror = (event: any) => {
      if (event.error === "no-speech") return;
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        setError("Microphone permission denied. Please allow mic access and try again.");
        enabledRef.current = false;
        setIsListening(false);
        return;
      }
      setError(`Speech recognition error: ${event.error}`);
    };

    recognition.onend = () => {
      setIsListening(false);
      // Auto-restart if still enabled (Chrome stops after silence)
      if (enabledRef.current) {
        setTimeout(() => {
          try {
            recognition.start();
            setIsListening(true);
          } catch {
            // already started
          }
        }, 100);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      enabledRef.current = false;
      try {
        recognition.stop();
      } catch {
        // already stopped
      }
    };
  }, [lang]);

  const start = useCallback(() => {
    if (!recognitionRef.current) return;
    setError(null);
    enabledRef.current = true;
    try {
      recognitionRef.current.start();
      setIsListening(true);
    } catch {
      // already started
    }
  }, []);

  const stop = useCallback(() => {
    enabledRef.current = false;
    setIsListening(false);
    setInterimTranscript("");
    try {
      recognitionRef.current?.stop();
    } catch {
      // already stopped
    }
  }, []);

  return { isListening, isSupported, error, start, stop, interimTranscript };
}
