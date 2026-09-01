# Sahayak Live — Pitch Script (English)

Complete judge-ready script, slide by slide. Use with `docs/pitch-deck.html`.

---

## 🎤 60-Second Elevator Pitch

> "Good morning judges. Imagine thirty children in a classroom, and only one teacher. Now imagine that behind every raised hand, every confused eyebrow, and every silent child too shy to ask — there is a second teacher. An AI that speaks, that listens, that whispers private help to the one child who needs it, and that tells the real teacher exactly where the class is falling behind — live, in the moment.
>
> That is Sahayak Live. We are not the eleventh tutoring app. We are the first AI *co-teacher* that lives inside the physical classroom. And here is how we do it."

---

## 📑 Slide-by-Slide Script

### Slide 1 — Title (Intro, ~30s)
> "Good morning, judges. This is Sahayak — in Sanskrit it literally means 'helper.' And that's exactly what we built: an AI that helps the teacher, not replaces them — even though every child gets their own personal tutor."

*Introduce your team + roles here.*

### Slide 2 — Problem (~45s)
> "A teacher can only be in one place at a time. In a class of 30 to 60, a teacher cannot answer every raised hand, cannot spot every confused face, and cannot give each child personal attention — while still teaching everyone.
>
> Over 60% of children are too afraid to ask a question — the shame of 'being slow' silences the very children who need help most. Each student gets less than a minute of individual attention per class. And about a third of the class is silently confused — the teacher only finds out at the next exam, when it's too late. Every tool that exists tutors the screen — not the room. The live classroom is empty."

### Slide 3 — Solution (~60s)
> "Sahayak fills that empty room. It's a third presence in the class.
>
> When a child asks a question, Sahayak answers out loud — voice-first, right in the flow of the lesson. When a student is confused, Sahayak privately flags the teacher — 'Rahul needs one minute on common denominators' — so the teacher can help without embarrassing the child. Our confusion radar watches the whole class: 'twelve of thirty students are confused right now,' told to the teacher mid-lesson, not at the exam.
>
> Because of our floor manager, the AI knows when to speak and when to stay quiet — it amplifies the teacher, never competes with them. Nine agents work together under one orchestrator: lesson context, replier, quiz master, whisper, gap radar, and insights — all running live."

### Slide 4 — Why Now / Market (~45s)
> "So why now? The market is already moving. AI in education is projected to reach 41 billion dollars by 2030. India has 260 million K-12 students across 1.5 million schools.
>
> Critically, NEP 2020 *mandates* digital classrooms. This is policy running toward us, not hype we're chasing. The whole edtech world has proven AI can teach — what nobody has done is put that AI inside the live classroom, beside the teacher, with a human voice."

### Slide 5 — USP (~45s)
> "Our unique value proposition, in one line: a voice AI that lives inside the physical classroom — whispering to each child, answering aloud, and turning thirty silent confusions into one teacher alert — while always deferring to the human teacher at the front of the room.
>
> Compared to Khanmigo, MagicSchool, and Squirrel AI — they're all tutors on a screen. None of them do live voice, turn-taking, private whispers, or live confusion clustering. We're not the eleventh tutor. We are the first co-teacher."

### Slide 6 — Technical Architecture (~60s)
> "Under the hood: a Next.js front end on the devices, sending voice to a real-time FastAPI WebSocket backend. A LangGraph orchestrator runs our nine specialized agents, each calling the best model — Groq, Mistral, Gemini, or local Ollama when offline.
>
> Critical: our voice is a *local neural* TTS, so the AI sounds human, not robotic — and the whole thing is offline-first, so a classroom runs on one laptop with no internet dependency. One shared mic, no phones, no wearables needed."

### Slide 7 — Business Model + Ask (~60s)
> "How we make money: per-classroom SaaS. Schools pay per classroom per year — from 35,000 rupees for fifteen classrooms, up to premium unlimited. At 85–95% gross margin, because inference costs us less than thirty dollars a year per classroom.
>
> The addressable market is over a thousand crore rupees across 50 to 80 thousand tech-forward private schools. Our moats: the hardware bundle that locks in schools, and a proprietary dataset of Indian classroom interactions that no one else has.
>
> We ask for fifty thousand dollars to run a 20-school pilot, tune our vertical math model, and ship bilingual Hindi-first voice.
>
> The room is empty. We get there first. Thank you."

---

## 🚦 Quick Cheat Sheet

| Slide | One line |
|---|---|
| Problem | "A teacher can't be everywhere — and the shyest kid is the one most behind." |
| Solution | "An AI co-teacher that speaks, whispers, and reads the whole class live." |
| Why now | "41B market, 260M students, NEP 2020 — the moment is now." |
| USP | "Not the 11th tutor — the first co-teacher that lives in the room." |
| Tech | "Next.js + FastAPI + LangGraph, 9 agents, offline-first, human neural voice." |
| Business | "Per-classroom SaaS, 85–95% margin, ₹1,000 Cr TAM, $50K ask." |

---

## 🔥 Likely Judge Questions + Answers

**Q: "Phones aren't allowed — how does this work?"**
> "We're phone-free and wearable-free. It runs on the teacher's laptop and the classroom's existing speaker. Students just speak — Sahayak listens and identifies them by voice. No gadgets on benches at all."

**Q: "How do you know a student's comment is a real question, not chatter?"**
> "Three layers: topic-aware filtering — it only processes speech that matches the current lesson; teacher control — the teacher opens the floor for questions; and our floor manager keeps the AI silent while teaching happens. Off-topic noise is ignored, just logged."

**Q: "How is this different from every other AI tutor?"**
> "Every other tool is a screen app for after school. We're the first to be inside the physical classroom, beside the teacher, in real time, with voice — and we don't need phones, wearables, or extra hardware."
