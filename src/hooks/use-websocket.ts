"use client";

import { useEffect, useRef, useCallback, useState } from "react";

type MessageHandler = (msg: Record<string, unknown>) => void;

export function useWebSocket(url: string | null, onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<"idle" | "connecting" | "connected" | "disconnected">("idle");
  const handlerRef = useRef(onMessage);
  handlerRef.current = onMessage;

  const connect = useCallback(() => {
    if (!url) return;
    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setStatus("connected");
    ws.onclose = () => {
      setStatus("disconnected");
      // Auto-reconnect after 2s
      setTimeout(() => {
        if (wsRef.current === ws) connect();
      }, 2000);
    };
    ws.onerror = () => setStatus("disconnected");
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        handlerRef.current(msg);
      } catch {
        // ignore malformed
      }
    };
  }, [url]);

  const send = useCallback((msg: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("idle");
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  return { status, send, disconnect, ws: wsRef };
}
