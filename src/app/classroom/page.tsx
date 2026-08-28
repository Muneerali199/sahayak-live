"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Mic, Users, GraduationCap, ArrowRight, Radio } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

export default function ClassroomLobby() {
  const router = useRouter();
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [role, setRole] = useState<"teacher" | "student">("teacher");
  const [joinCode, setJoinCode] = useState("");

  // Restore name from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("sahayak_name");
    if (saved) setName(saved);
  }, []);

  const createRoom = () => {
    if (!name.trim()) {
      toast({ title: "Please enter your name", variant: "destructive" });
      return;
    }
    localStorage.setItem("sahayak_name", name.trim());
    const roomId = `room-${Math.random().toString(36).slice(2, 8)}`;
    router.push(`/classroom/${roomId}?role=${role}&name=${encodeURIComponent(name.trim())}`);
  };

  const joinRoom = () => {
    if (!name.trim()) {
      toast({ title: "Please enter your name", variant: "destructive" });
      return;
    }
    if (!joinCode.trim()) {
      toast({ title: "Please enter a room code", variant: "destructive" });
      return;
    }
    localStorage.setItem("sahayak_name", name.trim());
    router.push(`/classroom/${joinCode.trim()}?role=student&name=${encodeURIComponent(name.trim())}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-950 to-slate-950 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-2xl"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-4 shadow-lg shadow-purple-500/30"
          >
            <Radio className="w-8 h-8 text-white" />
          </motion.div>
          <h1 className="text-4xl font-bold text-white mb-2">Sahayak Live</h1>
          <p className="text-indigo-300 text-lg">Multi-Agent Voice Co-Teacher for Live Classrooms</p>
        </div>

        <Card className="bg-white/5 backdrop-blur-xl border-white/10">
          <CardHeader>
            <CardTitle className="text-white text-2xl">Start or Join a Class</CardTitle>
            <CardDescription className="text-indigo-200">
              The AI co-teacher joins your live classroom, listens to the lesson, and helps students at the right moment.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Name input */}
            <div>
              <label className="text-sm font-medium text-indigo-200 mb-2 block">Your Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Mrs. Sharma"
                className="bg-white/10 border-white/20 text-white placeholder:text-white/40"
              />
            </div>

            {/* Role selection */}
            <div>
              <label className="text-sm font-medium text-indigo-200 mb-2 block">I am a...</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setRole("teacher")}
                  className={`flex items-center gap-3 p-4 rounded-xl border transition-all ${
                    role === "teacher"
                      ? "bg-indigo-500/30 border-indigo-400 ring-2 ring-indigo-400/50"
                      : "bg-white/5 border-white/10 hover:bg-white/10"
                  }`}
                >
                  <GraduationCap className="w-6 h-6 text-indigo-300" />
                  <div className="text-left">
                    <div className="text-white font-medium">Teacher</div>
                    <div className="text-xs text-indigo-300">Control the AI, run quizzes</div>
                  </div>
                </button>
                <button
                  onClick={() => setRole("student")}
                  className={`flex items-center gap-3 p-4 rounded-xl border transition-all ${
                    role === "student"
                      ? "bg-emerald-500/30 border-emerald-400 ring-2 ring-emerald-400/50"
                      : "bg-white/5 border-white/10 hover:bg-white/10"
                  }`}
                >
                  <Users className="w-6 h-6 text-emerald-300" />
                  <div className="text-left">
                    <div className="text-white font-medium">Student</div>
                    <div className="text-xs text-emerald-300">Ask questions, get help</div>
                  </div>
                </button>
              </div>
            </div>

            {/* Create room */}
            <div className="pt-2">
              <Button
                onClick={createRoom}
                className="w-full h-12 text-base bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
              >
                <Mic className="w-5 h-5 mr-2" />
                Start Live Classroom
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-white/10" />
              <span className="text-xs text-white/40">OR</span>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            {/* Join room */}
            <div className="flex gap-3">
              <Input
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value)}
                placeholder="Enter room code..."
                className="bg-white/10 border-white/20 text-white placeholder:text-white/40"
                onKeyDown={(e) => e.key === "Enter" && joinRoom()}
              />
              <Button
                onClick={joinRoom}
                variant="secondary"
                className="bg-white/10 border-white/20 text-white hover:bg-white/20"
              >
                Join
              </Button>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-white/30 text-sm mt-6">
          Powered by Multi-Agent LangGraph Orchestration · Groq + Mistral
        </p>
      </motion.div>
    </div>
  );
}
