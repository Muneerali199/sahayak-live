"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic, MicOff, Send, Volume2, VolumeX, Users, Brain, AlertTriangle,
  GraduationCap, Radio, Square, Zap, Eye, EyeOff, MessageSquare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { useWebSocket } from "@/hooks/use-websocket";
import { useSpeechRecognition } from "@/hooks/use-speech-recognition";
import { useAgora } from "@/hooks/use-agora";
import { speak, stopSpeaking } from "@/lib/tts";
import { useToast } from "@/hooks/use-toast";

interface TranscriptEntry {
  speaker_id: string;
  name: string;
  role: string;
  text: string;
  timestamp: string;
}

interface AgentEntry {
  agent: string;
  action: string;
  status: string;
  detail: string;
  timestamp: string;
}

interface Participant {
  user_id: string;
  name: string;
  role: string;
}

const AGENT_COLORS: Record<string, string> = {
  lesson_context: "text-blue-400",
  floor_manager: "text-amber-400",
  gap_radar: "text-red-400",
  differentiation: "text-purple-400",
  explainer: "text-emerald-400",
  quizmaster: "text-cyan-400",
  code_switch: "text-pink-400",
  insights: "text-indigo-400",
};

const AGENT_LABELS: Record<string, string> = {
  lesson_context: "Lesson Context",
  floor_manager: "Floor Manager",
  gap_radar: "Gap Radar",
  differentiation: "Differentiation",
  explainer: "Explainer",
  quizmaster: "Quizmaster",
  code_switch: "Code-Switch",
  insights: "Insights",
};

const FLOOR_BADGES: Record<string, { icon: string; label: string; color: string }> = {
  TEACHER_TALKING: { icon: "🟦", label: "Teacher speaking", color: "bg-blue-500/20 text-blue-300 border-blue-500/30" },
  STUDENT_TALKING: { icon: "🟩", label: "Student speaking", color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" },
  OPEN_FLOOR: { icon: "⬜", label: "Open floor", color: "bg-slate-500/20 text-slate-300 border-slate-500/30" },
  AI_SPEAKING: { icon: "🟪", label: "AI speaking", color: "bg-purple-500/20 text-purple-300 border-purple-500/30" },
};

export default function ClassroomRoom() {
  const params = useParams();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const roomId = params.id as string;
  const role = (searchParams.get("role") || "student") as "teacher" | "student";
  const name = searchParams.get("name") || "Anonymous";
  const userId = useRef(`u-${Math.random().toString(36).slice(2, 8)}`).current;

  // ─── State ──────────────────────────────────────────────
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [floorState, setFloorState] = useState("OPEN_FLOOR");
  const [floorBadge, setFloorBadge] = useState("⬜ Open floor");
  const [aiPermitted, setAiPermitted] = useState(false);
  const [agentLog, setAgentLog] = useState<AgentEntry[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [aiMuted, setAiMuted] = useState(false);
  const [gapAlert, setGapAlert] = useState<{ concept: string; students: string[]; count: number } | null>(null);
  const [aiCaption, setAiCaption] = useState("");
  const [textInput, setTextInput] = useState("");
  const [showSwarm, setShowSwarm] = useState(true);
  const [sessionEnded, setSessionEnded] = useState(false);
  const [insights, setInsights] = useState<any>(null);
  const [quizActive, setQuizActive] = useState(false);
  const [quizTarget, setQuizTarget] = useState("");
  const [liveAudio, setLiveAudio] = useState(false);

  const transcriptEndRef = useRef<HTMLDivElement>(null);

  // ─── WebSocket ──────────────────────────────────────────
  const wsUrl = `ws://127.0.0.1:8001/ws/classroom/${roomId}`;
  const joinedRef = useRef(false);

  const handleMessage = useCallback((msg: Record<string, unknown>) => {
    const type = msg.type as string;

    switch (type) {
      case "JOINED":
        setParticipants((msg.participants as Participant[]) || []);
        break;
      case "PARTICIPANT_JOINED":
      case "PARTICIPANT_LEFT":
        setParticipants((msg.participants as Participant[]) || []);
        break;
      case "UTTERANCE":
        setTranscript((prev) => [...prev, msg as unknown as TranscriptEntry]);
        break;
      case "FLOOR_STATE":
        setFloorState(msg.state as string);
        setFloorBadge(msg.badge as string);
        setAiPermitted(msg.ai_permitted as boolean);
        break;
      case "AI_SPEAK":
        const content = msg.content as string;
        setAiCaption(content);
        if (!msg.via_channel) speak(content);
        setTimeout(() => setAiCaption(""), 5000);
        break;
      case "WHISPER":
        const whisperContent = msg.content as string;
        setAiCaption(`(private) ${whisperContent}`);
        speak(whisperContent);
        setTimeout(() => setAiCaption(""), 5000);
        toast({ title: " Private help from Sahayak", description: whisperContent.slice(0, 100) });
        break;
      case "GAP_ALERT":
        setGapAlert({
          concept: msg.concept as string,
          students: msg.students as string[],
          count: msg.count as number,
        });
        toast({
          title: " Common Gap Detected",
          description: `${msg.concept} — ${msg.count} students struggling`,
          variant: "destructive",
        });
        setTimeout(() => setGapAlert(null), 8000);
        break;
      case "AGENT_LOG":
        setAgentLog((prev) => [...prev, ...(msg.agents as AgentEntry[])].slice(-20));
        break;
      case "AI_MUTED":
        setAiMuted(msg.muted as boolean);
        break;
      case "QUIZ_ASK":
        setQuizActive(true);
        setQuizTarget(msg.target_student_id as string);
        setAiCaption(`Quiz for ${msg.target_name}: ${msg.content}`);
        if (!msg.via_channel) speak(msg.content as string);
        break;
      case "QUIZ_RESULT":
        setQuizActive(false);
        setAiCaption(msg.content as string);
        if (!msg.via_channel) speak(msg.content as string);
        setTimeout(() => setAiCaption(""), 5000);
        break;
      case "SESSION_ENDED":
        setSessionEnded(true);
        setInsights(msg.insights);
        stopSpeaking();
        break;
    }
  }, [toast]);

  const { status, send } = useWebSocket(wsUrl, handleMessage);

  // ─── Live classroom audio (Agora RTC) ───────────────────
  const {
    status: agoraStatus,
    peers: agoraPeers,
    error: agoraError,
  } = useAgora({
    channel: `sahayak-${roomId}`,
    uid: userId,
    role,
    enabled: liveAudio,
  });

  // Tell the backend whether this participant is in the live audio channel so
  // it knows when to broadcast Sahayak's voice into it.
  useEffect(() => {
    if (status !== "connected") return;
    send({ type: "LIVE_AUDIO", enabled: agoraStatus === "joined" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agoraStatus, status]);

  // Join once connected
  useEffect(() => {
    if (status === "connected" && !joinedRef.current) {
      joinedRef.current = true;
      send({ type: "JOIN", user_id: userId, name, role });
    }
  }, [status, send, userId, name, role]);

  // ─── Speech Recognition ─────────────────────────────────
  const handleFinalResult = useCallback((text: string) => {
    send({ type: "UTTERANCE", text, is_final: true });
  }, [send]);

  const { isListening, isSupported, error: speechError, start: startListening, stop: stopListening, interimTranscript } =
    useSpeechRecognition(handleFinalResult);

  // ─── Auto-scroll transcript ─────────────────────────────
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript, interimTranscript]);

  // ─── Teacher Controls ───────────────────────────────────
  const toggleMute = () => {
    send({ type: "TEACHER_CONTROL", action: aiMuted ? "unmute" : "mute" });
  };

  const endClass = () => {
    send({ type: "TEACHER_CONTROL", action: "end_class" });
  };

  const runQuiz = (studentId: string) => {
    send({ type: "TEACHER_CONTROL", action: "quiz", target_student_id: studentId });
  };

  const sendText = () => {
    if (!textInput.trim()) return;
    send({ type: "UTTERANCE", text: textInput.trim(), is_final: true });
    setTextInput("");
  };

  // ─── Render ─────────────────────────────────────────────
  const floorInfo = FLOOR_BADGES[floorState] || FLOOR_BADGES.OPEN_FLOOR;
  const students = participants.filter((p) => p.role === "student");

  if (sessionEnded && insights) {
    return <SummaryView roomId={roomId} insights={insights} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 text-white">
      {/* ─── Header ─────────────────────────────────────── */}
      <div className="border-b border-white/10 bg-black/20 backdrop-blur-xl sticky top-0 z-50">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Radio className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg">Sahayak Live</h1>
              <p className="text-xs text-white/50">Room: {roomId}</p>
            </div>
          </div>

          {/* Floor State Badge */}
          <motion.div
            key={floorState}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`px-4 py-2 rounded-full border ${floorInfo.color} font-medium text-sm flex items-center gap-2`}
          >
            <span className="text-lg">{floorInfo.icon}</span>
            {floorInfo.label}
            {aiPermitted && !aiMuted && floorState !== "AI_SPEAKING" && (
              <span className="text-xs bg-purple-500/30 px-2 py-0.5 rounded-full ml-1">AI ready</span>
            )}
          </motion.div>

          {/* Connection + live audio */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={liveAudio ? "default" : "ghost"}
              onClick={() => setLiveAudio(!liveAudio)}
              className={liveAudio ? "bg-emerald-600 text-white" : "text-white/70 hover:bg-white/10"}
              title="Join/leave the live classroom audio channel"
            >
              <Radio className={`w-4 h-4 mr-1 ${agoraStatus === "joined" ? "animate-pulse" : ""}`} />
              {agoraStatus === "joined"
                ? `Live · ${agoraPeers.length + 1} in audio`
                : agoraStatus === "joining"
                ? "Joining audio..."
                : "Live Audio"}
            </Button>
            <div className={`w-2 h-2 rounded-full ${status === "connected" ? "bg-green-400" : "bg-red-400"}`} />
            <span className="text-xs text-white/50">
              {status === "connected" ? "Connected" : "Connecting..."}
            </span>
          </div>
        </div>
      </div>

      {/* ─── AI Caption Bar ─────────────────────────────── */}
      <AnimatePresence>
        {aiCaption && (
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
            className="bg-purple-500/20 border-b border-purple-500/30 px-4 py-3 flex items-center gap-3"
          >
            <Volume2 className="w-5 h-5 text-purple-300 shrink-0" />
            <p className="text-purple-100 text-sm flex-1">{aiCaption}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Gap Alert Banner ───────────────────────────── */}
      <AnimatePresence>
        {gapAlert && (
          <motion.div
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -100, opacity: 0 }}
            className="bg-red-500/20 border-b border-red-500/30 px-4 py-3 flex items-center gap-3"
          >
            <AlertTriangle className="w-5 h-5 text-red-300 shrink-0" />
            <div className="flex-1">
              <p className="text-red-100 font-medium text-sm">Common Gap: {gapAlert.concept}</p>
              <p className="text-red-200/70 text-xs">{gapAlert.count} students struggling — {gapAlert.students.join(", ")}</p>
            </div>
            {role === "teacher" && (
              <Button
                size="sm"
                className="bg-red-500/30 border-red-400/30 hover:bg-red-500/40 text-red-100"
                onClick={() => {
                  // The AI will auto-explain on next open floor
                  toast({ title: "AI will explain at the next pause" });
                }}
              >
                <Zap className="w-3 h-3 mr-1" /> Let AI explain
              </Button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Main Layout ────────────────────────────────── */}
      <div className="flex h-[calc(100vh-140px)]">
        {/* Left: Participants */}
        <div className="w-56 border-r border-white/10 bg-black/10 p-3 hidden md:block">
          <h3 className="text-xs font-medium text-white/40 uppercase mb-3 flex items-center gap-1">
            <Users className="w-3 h-3" /> Participants ({participants.length})
          </h3>
          <div className="space-y-2">
            {participants.map((p) => (
              <div key={p.user_id} className="flex items-center gap-2 p-2 rounded-lg bg-white/5">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                  p.role === "teacher" ? "bg-blue-500/30" : "bg-emerald-500/30"
                }`}>
                  {p.role === "teacher" ? <GraduationCap className="w-4 h-4" /> : p.name[0]?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{p.name}</p>
                  <p className="text-xs text-white/40 capitalize">{p.role}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Teacher quiz controls */}
          {role === "teacher" && students.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <h4 className="text-xs font-medium text-white/40 uppercase mb-2">Quick Quiz</h4>
              <div className="space-y-1">
                {students.map((s) => (
                  <Button
                    key={s.user_id}
                    size="sm"
                    variant="ghost"
                    className="w-full justify-start text-xs text-white/70 hover:bg-white/10"
                    onClick={() => runQuiz(s.user_id)}
                  >
                    <Brain className="w-3 h-3 mr-1" /> Quiz {s.name}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Center: Transcript */}
        <div className="flex-1 flex flex-col">
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-3 max-w-3xl mx-auto">
              {transcript.length === 0 && (
                <div className="text-center text-white/30 mt-20">
                  <Mic className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Waiting for the lesson to begin...</p>
                  <p className="text-xs mt-1">Turn on your mic to start</p>
                </div>
              )}
              {transcript.map((entry, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 ${entry.role === "teacher" ? "justify-start" : entry.role === "ai" ? "justify-center" : "justify-end"}`}
                >
                  <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    entry.role === "teacher"
                      ? "bg-blue-500/15 border border-blue-500/20"
                      : entry.role === "ai"
                      ? "bg-purple-500/20 border border-purple-500/30"
                      : "bg-emerald-500/15 border border-emerald-500/20"
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-medium ${
                        entry.role === "teacher" ? "text-blue-300" : entry.role === "ai" ? "text-purple-300" : "text-emerald-300"
                      }`}>
                        {entry.role === "ai" ? "Sahayak AI" : entry.name}
                      </span>
                      <Badge variant="outline" className="text-[10px] py-0 px-1.5 capitalize border-white/20 text-white/50">
                        {entry.role}
                      </Badge>
                    </div>
                    <p className="text-sm text-white/90">{entry.text}</p>
                  </div>
                </motion.div>
              ))}

              {/* Interim transcript */}
              {interimTranscript && (
                <div className={`flex gap-3 ${role === "teacher" ? "justify-start" : "justify-end"} opacity-50`}>
                  <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white/5 border border-white/10">
                    <p className="text-sm text-white/60 italic">{interimTranscript}...</p>
                  </div>
                </div>
              )}
              <div ref={transcriptEndRef} />
            </div>
          </ScrollArea>

          {/* Input bar */}
          <div className="border-t border-white/10 p-3 bg-black/20">
            <div className="flex items-center gap-2 max-w-3xl mx-auto">
              {/* Mic button */}
              <Button
                onClick={isListening ? stopListening : startListening}
                className={`shrink-0 ${
                  isListening
                    ? "bg-red-500 hover:bg-red-600 text-white"
                    : "bg-indigo-500 hover:bg-indigo-600 text-white"
                }`}
                size="icon"
                disabled={!isSupported}
                title={isSupported ? "Toggle microphone" : "Speech recognition not supported"}
              >
                {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </Button>

              {/* Text input fallback */}
              <Input
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder={isListening ? "Listening... type to send a message" : "Type a message for Sahayak (AI) or the teacher... press Enter"}
                className="bg-white/10 border-white/20 text-white placeholder:text-white/30"
                onKeyDown={(e) => e.key === "Enter" && sendText()}
              />
              <Button
                onClick={sendText}
                size="icon"
                className="shrink-0 bg-white/10 hover:bg-white/20 text-white"
                title="Send message"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            {speechError && (
              <p className="text-xs text-red-400 mt-1 text-center">{speechError}</p>
            )}
            {agoraError && (
              <p className="text-xs text-amber-400 mt-1 text-center">Live audio: {agoraError}</p>
            )}
          </div>
        </div>

        {/* Right: Agent Swarm Panel */}
        <div className="w-64 border-l border-white/10 bg-black/10 p-3 hidden lg:block">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-medium text-white/40 uppercase flex items-center gap-1">
              <Brain className="w-3 h-3" /> Agent Swarm
            </h3>
            <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => setShowSwarm(!showSwarm)}>
              {showSwarm ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
            </Button>
          </div>

          {showSwarm && (
            <div className="space-y-1.5">
              {Object.entries(AGENT_LABELS).map(([key, label]) => {
                const isActive = agentLog.some((a) => a.agent === key && a.status !== "error");
                const lastEntry = agentLog.findLast((a) => a.agent === key);
                return (
                  <motion.div
                    key={key}
                    animate={isActive ? { boxShadow: "0 0 8px rgba(99, 102, 241, 0.3)" } : {}}
                    className={`p-2 rounded-lg border transition-all ${
                      isActive
                        ? "bg-white/10 border-white/20"
                        : "bg-white/5 border-white/5 opacity-50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${isActive ? "bg-indigo-400 animate-pulse" : "bg-white/20"}`} />
                      <span className={`text-xs font-medium ${AGENT_COLORS[key] || "text-white/60"}`}>{label}</span>
                    </div>
                    {lastEntry && (
                      <p className="text-[10px] text-white/40 mt-1 truncate">{lastEntry.detail}</p>
                    )}
                  </motion.div>
                );
              })}
            </div>
          )}

          {/* Lesson context summary */}
          {agentLog.length > 0 && (
            <div className="mt-4 pt-3 border-t border-white/10">
              <h4 className="text-xs font-medium text-white/40 uppercase mb-2 flex items-center gap-1">
                <MessageSquare className="w-3 h-3" /> Lesson Context
              </h4>
              <p className="text-xs text-white/50 leading-relaxed">
                {agentLog.findLast((a) => a.agent === "lesson_context")?.detail || "Building context..."}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ─── Teacher Control Bar ─────────────────────────── */}
      {role === "teacher" && (
        <div className="border-t border-white/10 bg-black/30 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={aiMuted ? "default" : "ghost"}
              onClick={toggleMute}
              className={aiMuted ? "bg-red-500 text-white" : "text-white/70 hover:bg-white/10"}
            >
              {aiMuted ? <VolumeX className="w-4 h-4 mr-1" /> : <Volume2 className="w-4 h-4 mr-1" />}
              {aiMuted ? "AI Muted" : "AI Active"}
            </Button>
            <span className="text-xs text-white/30">Say "sahayak stop" to shush the AI</span>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={endClass}
            className="text-red-400 hover:bg-red-500/10"
          >
            <Square className="w-3 h-3 mr-1" /> End Class
          </Button>
        </div>
      )}
    </div>
  );
}

// ─── Summary View (inline for now) ─────────────────────────
function SummaryView({ roomId, insights }: { roomId: string; insights: any }) {
  const studentInsights = insights?.insights?.student_insights || [];
  const commonGaps = insights?.insights?.common_gaps || [];
  const recommendations = insights?.insights?.class_recommendations || [];
  const summary = insights?.insights?.summary || "Class completed.";
  const keyMoments = insights?.insights?.key_moments || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 text-white p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Post-Class Summary</h1>
          <p className="text-white/50">Room: {roomId}</p>
        </div>

        <Card className="bg-white/5 border-white/10 p-6 mb-4">
          <h2 className="text-lg font-semibold mb-2">Overview</h2>
          <p className="text-white/70">{summary}</p>
        </Card>

        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <Card className="bg-white/5 border-white/10 p-6">
            <h2 className="text-lg font-semibold mb-3">Student Insights</h2>
            <div className="space-y-3">
              {studentInsights.map((s: any, i: number) => (
                <div key={i} className="p-3 rounded-lg bg-white/5">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{s.name}</span>
                    <Badge variant="outline" className="border-white/20 text-white/60">{s.level}</Badge>
                  </div>
                  <p className="text-xs text-white/50">Comprehension: {Math.round((s.comprehension_score || 0) * 100)}%</p>
                  {s.gaps?.length > 0 && (
                    <p className="text-xs text-red-300/70 mt-1">Gaps: {s.gaps.join(", ")}</p>
                  )}
                  <p className="text-xs text-white/40 mt-1">{s.recommendation}</p>
                </div>
              ))}
              {studentInsights.length === 0 && <p className="text-white/30 text-sm">No student data.</p>}
            </div>
          </Card>

          <Card className="bg-white/5 border-white/10 p-6">
            <h2 className="text-lg font-semibold mb-3">Common Gaps</h2>
            <div className="space-y-2">
              {commonGaps.map((g: any, i: number) => (
                <div key={i} className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                  <p className="font-medium text-sm">{g.concept}</p>
                  <p className="text-xs text-white/50">Students: {g.students?.join(", ")}</p>
                  <p className="text-xs text-white/40 mt-1">{g.recommended_remediation}</p>
                </div>
              ))}
              {commonGaps.length === 0 && <p className="text-white/30 text-sm">No common gaps detected.</p>}
            </div>
          </Card>
        </div>

        <Card className="bg-white/5 border-white/10 p-6 mb-4">
          <h2 className="text-lg font-semibold mb-3">Recommendations</h2>
          <ul className="space-y-2">
            {recommendations.map((r: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm text-white/70">
                <span className="text-indigo-400 mt-0.5">→</span> {r}
              </li>
            ))}
          </ul>
        </Card>

        {keyMoments.length > 0 && (
          <Card className="bg-white/5 border-white/10 p-6">
            <h2 className="text-lg font-semibold mb-3">Key Moments</h2>
            <div className="space-y-2">
              {keyMoments.map((m: any, i: number) => (
                <p key={i} className="text-sm text-white/60">• {typeof m === "string" ? m : m.description || JSON.stringify(m)}</p>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
