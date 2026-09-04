"use client";

// Live classroom audio via Agora RTC. Each participant joins the room's
// channel so everyone (teacher + students) shares the same audio, and the AI
// co-teacher's voice can be broadcast into it by the backend.

import { useCallback, useEffect, useRef, useState } from "react";
import type { IAgoraRTCClient, ILocalAudioTrack } from "agora-rtc-sdk-ng";

const BACKEND = "http://127.0.0.1:8001";

type AgoraStatus = "idle" | "joining" | "joined" | "error";

interface UseAgoraOptions {
  channel: string;
  uid: string;
  role: "teacher" | "student";
  enabled: boolean;
}

// Agora RTC touches `window` at import time, so load it lazily in the browser
// only (keeps the room page SSR-safe).
async function loadAgora() {
  if (typeof window === "undefined") return null;
  const mod = await import("agora-rtc-sdk-ng");
  return mod.default as typeof import("agora-rtc-sdk-ng")["default"];
}

export function useAgora({ channel, uid, role, enabled }: UseAgoraOptions) {
  const clientRef = useRef<IAgoraRTCClient | null>(null);
  const micTrackRef = useRef<ILocalAudioTrack | null>(null);
  const [status, setStatus] = useState<AgoraStatus>("idle");
  const [peers, setPeers] = useState<number[]>([]);
  const [error, setError] = useState("");

  const leave = useCallback(async () => {
    const client = clientRef.current;
    clientRef.current = null;
    micTrackRef.current?.close();
    micTrackRef.current = null;
    if (!client) {
      setStatus("idle");
      setPeers([]);
      return;
    }
    try {
      await client.leave();
    } catch {
      /* ignore */
    }
    client.remoteUsers.forEach((u) => u.audioTrack?.stop());
    client.removeAllListeners();
    setStatus("idle");
    setPeers([]);
  }, []);

  const join = useCallback(async () => {
    if (clientRef.current) return;
    const AgoraRTC = await loadAgora();
    if (!AgoraRTC) return;

    const safeChannel = channel.replace(/[^a-zA-Z0-9_\-\.]/g, "-").slice(0, 50);
    const numericUid = Array.from(uid).reduce((acc, c) => acc + c.charCodeAt(0), 0) % 1e9 || 1;
    const isTeacher = role === "teacher";

    try {
      setStatus("joining");
      setError("");

      const res = await fetch(`${BACKEND}/api/agora/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: safeChannel, uid: numericUid, role: "publisher" }),
      });
      const data = await res.json();
      if (!res.ok || !data.token) throw new Error(data.error || "Failed to get Agora token");

      const client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });
      clientRef.current = client;

      client.on("user-joined", (user) => {
        setPeers((prev) => (prev.includes(user.uid as number) ? prev : [...prev, user.uid as number]));
      });
      client.on("user-left", (user) => {
        setPeers((prev) => prev.filter((u) => u !== user.uid));
        user.audioTrack?.stop();
      });
      client.on("user-published", async (user, mediaType) => {
        if (mediaType !== "audio") return;
        await client.subscribe(user, mediaType);
        user.audioTrack?.play();
      });
      client.on("user-unpublished", (user, mediaType) => {
        if (mediaType === "audio") user.audioTrack?.stop();
      });

      await client.join(data.app_id, safeChannel, data.token, numericUid);

      if (isTeacher) {
        const track = await AgoraRTC.createMicrophoneAudioTrack({ encoderConfig: "speech_standard" });
        await client.publish([track]);
        micTrackRef.current = track;
      }

      setStatus("joined");
    } catch (e) {
      setStatus("error");
      setError(e instanceof Error ? e.message : String(e));
      if (clientRef.current) clientRef.current.removeAllListeners();
      clientRef.current = null;
    }
  }, [channel, uid, role]);

  useEffect(() => {
    if (!enabled) {
      if (clientRef.current) leave();
      return;
    }
    if (status === "idle" || status === "error") join();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, channel]);

  useEffect(() => {
    return () => {
      micTrackRef.current?.close();
      micTrackRef.current = null;
      if (clientRef.current) {
        clientRef.current.leave().catch(() => {});
      }
    };
  }, []);

  return { status, peers, error, join, leave };
}