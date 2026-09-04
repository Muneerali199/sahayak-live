# 🎓 Sahayak Live — Multi-Agent Voice Co-Teacher

### A voice AI co-teacher that participates in a live digital classroom, waits for the right moment to speak, and helps students without interrupting the teacher.

Built on [Sahayak-Teacher](https://github.com/Muneerali199/sahayak-teacher) with a new multi-agent LangGraph backend. Designed for **PS31**.

---

## 🏆 The USP — Three Things No Competitor Has

### 1. 🚦 The Floor Manager (Turn-Taking State Machine)
A dedicated agent models the classroom "conversation floor" as a live state machine:
`TEACHER_TALKING` → AI stays silent · `STUDENT_TALKING` → AI stays silent · `OPEN_FLOOR` → AI may speak

The AI is **physically gated** by this — it cannot interrupt the teacher. A visible badge shows the floor state in real-time so judges **see** the AI waiting politely.

### 2. 📡 Gap Radar (Live Common-Misunderstanding Clustering)
Continuously scans student utterances for confusion signals and **clusters them by concept**. When 2+ students struggle with the same concept, it fires a **"Common Gap Detected"** alert and queues a simpler explanation for the next open-floor moment.

### 3. 🤫 Whisper Tutor (Dual-Mode AI: Broadcast + Private)
The same AI is simultaneously a class co-teacher (broadcasts to everyone) **and** a per-student private tutor. When one student is confused but the teacher is mid-sentence, the AI sends a targeted simpler explanation to **only that student's screen** — without interrupting the class.

---

## 🧠 The 9 Agents

| Agent | Job |
|---|---|
| **Lesson Context** | Rolling summary of the ongoing lesson topic and concepts |
| **Floor Manager** ⭐ | Turn-taking FSM — gates every AI action on floor state |
| **Gap Radar** ⭐ | Clusters student confusion by concept, fires common-gap alerts |
| **Differentiation Engine** | Per-student comprehension profiling (beginner/intermediate/advanced) |
| **Explainer** | Generates calibrated explanations at 3 difficulty levels |
| **Replier** | Answers direct student questions & greetings conversationally when the floor is open |
| **Quizmaster** | Spoken quizzes — asks out loud, names a student, listens, evaluates |
| **Code-Switch** | Detects Hinglish/Tamil-English mixing, makes AI reply in matching language |
| **Insights** | Post-class: per-student gaps, common gaps, who needs support, next steps |

**Orchestrator:** LangGraph `StateGraph` — Ingest → Lesson Context → Code-Switch → Gap Radar → Differentiation → Floor Manager → Router (Quiz → Whisper → Reply) → Action

---

## ⚡ Quick Start

### 1. Backend (the multi-agent brain)

```bash
cd backend/classroom
pip install -r requirements.txt
cp .env.example .env   # fill in Groq + Mistral keys
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Verify: `curl http://127.0.0.1:8001/api/health`

> **Optional — human-like voice (recommended):** the AI speaks with a *local neural* TTS
> (Piper) so it sounds human instead of robotic. Run `bash scripts/setup_piper.sh` once
> (creates `piper-venv/` + downloads the Amy voice). Without it, the backend falls back
> to the macOS `say` voice. No API key needed either way.

> **Optional — live classroom audio (Agora RTC):** teacher + students share one live
> audio channel so the whole class hears the same mic (and the AI voice plays through
> the room speaker). One-time setup:
> `pip install --break-system-packages --user agora-token-builder`, then
> `agora login` → `agora project create sahayak-live --feature rtc` →
> `agora project env write` and paste `AGORA_APP_ID` / `AGORA_APP_CERTIFICATE` into
> `backend/classroom/.env`. Frontend just clicks the **Live Audio** toggle.

### 2. Frontend (the classroom UI)

```bash
npm install
npm run dev    # http://localhost:9002
```

### 3. Go Live

1. Open `http://localhost:9002/classroom`
2. Enter your name, select **Teacher**, click **Start Live Classroom**
3. Allow microphone access
4. Start teaching — the AI listens and helps at the right moments
5. Open another browser tab as a student: `http://localhost:9002/classroom/<room-code>?role=student&name=Rahul`
6. Click **Live Audio** in the header to share the classroom audio channel with everyone

---

## 🔑 API Keys (any ONE works)

Add to `backend/classroom/.env`:

```ini
GROQ_API_KEY=           # https://console.groq.com/keys
MISTRAL_API_KEY=        # https://console.mistral.ai
GEMINI_API_KEY=         # https://aistudio.google.com/apikey (optional)
```

Priority: Gemini → Mistral → Groq → **local Ollama** (fully offline, final fallback). Auto-fallback on errors.

---

## 🎬 3-Minute Demo Script

**Subject: Math — Fractions.** Students: Aarav (advanced), Priya (intermediate), Rahul (beginner).

1. **Teacher** explains adding fractions with different denominators
2. **Rahul** says "I don't understand, why can't I just add the tops and bottoms?"
3. **Gap Radar** lights up: "1 individual gap detected"
4. **Rahul** asks again: "I'm still confused about common denominators"
5. **Gap Radar**: "2 individual gaps" → **Whisper Tutor** sends private explanation to Rahul's screen only (teacher not interrupted)
6. **Teacher** clicks **"Quiz Priya"** → **Quizmaster** asks Priya a question out loud
7. **Priya** answers → **Quizmaster** evaluates and gives feedback
8. **Teacher** clicks **"End Class"** → **Insights** generates: Rahul needs support on common denominators; class gap: LCM; recommended next lesson

**Money line:** *"Every AI tool helps teachers plan lessons. Ours sits next to them in class."*

---

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Status + configured providers |
| `GET` | `/api/rooms` | List active rooms |
| `WS` | `/ws/classroom/{room_id}` | Realtime classroom connection |
| `POST` | `/api/rooms/{id}/end` | End session + generate insights |
| `GET` | `/api/rooms/{id}/insights` | Get post-class insights |
| `GET` | `/api/rooms/{id}/state` | Debug: current classroom state |
| `GET` | `/api/tts?text=...&lang=en-IN` | Human-like speech audio (WAV) |
| `POST` | `/api/agora/token` | Mint an Agora RTC token for the live audio channel |

---

## 🏗️ Architecture

```
Next.js 15 Frontend                    Python FastAPI + LangGraph Backend
┌──────────────────────┐               ┌──────────────────────────────┐
│ /classroom (lobby)   │─── WebSocket──│ /ws/classroom/{room_id}      │
│ /classroom/[id]      │               │                              │
│   - Floor badge      │               │  ClassroomOrchestrator       │
│   - Transcript       │               │  (LangGraph StateGraph):     │
│   - Agent swarm      │               │                              │
│   - Teacher controls │               │  Ingest → Context →          │
│   - Whisper toasts   │               │  CodeSwitch → GapRadar →     │
│   - Live audio (mic) │── Agora RTC ──│  Differentiation →           │
│     → shared channel │               │  FloorManager → Router →     │
│ /classroom/[id]/sum  │─── REST ─────│  Action                      │
│   (post-class)       │               │  FloorManager → Router →     │
└──────────────────────┘               │  Action                      │
                                       │                              │
                                       │  8 agents via llm_client    │
                                       │  (Groq + Mistral + fallback) │
                                       └──────────────────────────────┘
```

## 📁 Project Structure

```
sahayak-live/
├── src/                           # Next.js 15 frontend (from Sahayak-Teacher)
│   ├── app/
│   │   ├── classroom/             # NEW: live classroom
│   │   │   ├── page.tsx           #   lobby (create/join room)
│   │   │   └── [id]/page.tsx      #   room view + summary view
│   │   └── dashboard/             # existing prep tools + Go Live CTA
│   ├── hooks/
│   │   ├── use-websocket.ts       # NEW: WebSocket hook
│   │   ├── use-agora.ts           # NEW: live classroom audio (Agora RTC)
│   │   └── use-speech-recognition.ts # NEW: Web Speech API hook
│   └── lib/
│       └── tts.ts                 # NEW: text-to-speech manager
└── backend/classroom/             # NEW: multi-agent backend
    ├── main.py                    # FastAPI + WebSocket room manager
    ├── orchestrator.py            # LangGraph StateGraph
    ├── state.py                   # ClassroomState schema
    ├── room.py                    # Room registry + participants
    ├── llm_client.py              # Groq/Mistral/Gemini router + fallback
    ├── tts.py                     # human-like TTS (Piper) + text humanizer
    ├── requirements.txt
    ├── .env.example
    └── agents/
        ├── floor_manager.py       # ⭐ turn-taking FSM
        ├── lesson_context.py      # rolling lesson summary
        ├── gap_radar.py           # ⭐ confusion clustering
        ├── differentiation.py     # per-student levels
        ├── explainer.py           # 3-level explanations
        ├── replier.py             # direct Q&A / greeting replies
        ├── quizmaster.py          # spoken quizzes
        ├── code_switch.py         # multilingual detection
        └── insights.py            # post-class summary
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind, Framer Motion, ShadCN UI |
| Backend | Python, FastAPI, uvicorn, WebSockets + server-minted Agora tokens |
| Orchestration | LangGraph StateGraph |
| LLM | Groq (GPT-OSS-120B), Mistral (mistral-small-latest), Gemini (optional), Ollama (local/offline) |
| Speech → text | Web Speech API (SpeechRecognition) |
| Voice (TTS) | **Piper local neural TTS** (human voice) + macOS `say` fallback |
| Live audio | Agora RTC (`agora-rtc-sdk-ng`, `agora-token-builder`) |

---

## 📊 PS31 Requirement Coverage

| Requirement | Solution |
|---|---|
| Real-time participation | WebSocket transcript loop |
| Awareness of teacher/student roles | Role-tagged participants |
| Appropriate turn-taking | **Floor Manager FSM** (visible badge) |
| Contextual answers | **Lesson Context** agent (rolling summary) |
| Different explanation levels | **Differentiation Engine** + **Explainer** (3 levels) |
| Spoken quizzes | **Quizmaster** agent (TTS + STT) |
| Multilingual / code-switched | **Code-Switch** agent (Hinglish, Tamil-English, etc.) |
| Student identification | Firebase Auth + room identity + per-student profiles |
| Post-class summaries | **Insights** agent + summary page |
| Teacher control / override | Mute toggle, End Class, quiz controls |

## 🚀 Market & Business Model

The combination of **live voice + floor management + private whispering + confusion clustering is genuinely novel** — no production product, funded startup, or published prototype ships it together (Khanmigo, MagicSchool, Century Tech and Robyn are the closest, and none do all four).

- **Market:** AI-in-education is $6.9B → $41B by 2030 (41% CAGR); India K-12 EdTech $6.5B → $29B (~28% CAGR).
- **Model:** Per-classroom SaaS at ₹15,000–60,000/yr (India) / $360–1,200/yr (US), 85–95% gross margin (inference via Groq is near-free).
- **Moats:** voice-first physical presence, a proprietary dataset of Indian classroom interactions, hardware lock-in, and Hindi/Tamil/Telugu/Marathi/Bengali voice coverage no competitor serves.

Full research + pricing + go-to-market: **[docs/business-model.md](docs/business-model.md)**

## 📊 Pitch Materials

- **Slide deck (7 slides):** `docs/pitch-deck.html` — open in any browser, navigate with arrow keys / Prev-Next. Includes problem, solution, market, USP, technical architecture (Mermaid diagram + tech stack), business model and ask.
- **Pitch script:** `docs/pitch-script.md` — 60-second elevator pitch, slide-by-slide script, judge Q&A.
- **Business model:** `docs/business-model.md` — market research, pricing, GTM, moats.

## 📄 License

MIT. Built on [Sahayak-Teacher](https://github.com/Muneerali199/sahayak-teacher) by Muneer Ali.
