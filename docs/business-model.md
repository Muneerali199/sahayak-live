# Sahayak Live — Market Research & Business Model

## 1. Uniqueness Validation — Is This Idea Novel?

**Deep research (TechCrunch, Product Hunt, LinkedIn, academic papers) confirms: NO production product, funded startup, or published prototype combines live voice + physical classroom + floor management + private whispering + confusion clustering simultaneously.**

### What everyone else does

| Product | Live voice in class? | Floor mgmt | Private whisper | Confusion clustering |
|---|---|---|---|---|
| **Khanmigo** | ❌ text, async tutor | ❌ | ❌ | ❌ |
| **MagicSchool** | ❌ prep tools only | ❌ | ❌ | ❌ |
| **Century Tech** | ❌ LMS | ❌ | ❌ | ❌ |
| **Cognii** | ❌ text assessment | ❌ | ❌ | ❌ |
| **Robyn Robot** (UK) | ✅ physical, 200+ classrooms | ❌ reactive only | ❌ shared devices | ❌ |
| **Lumina** (SG hkathon) | ✅ | ⚠️ partial | ❌ | ⚠️ off-topic only |
| **TA-DA** (hkathon) | ❌ text | ❌ | ❌ | ⚠️ self-reported |
| **KakshAI / Cognivise** (hkathon) | ✅ | ❌ | ❌ | ❌ |

**The fundamental gap:** Every product is either a *teacher-facing prep tool* OR an *asynchronous student tutor*. **Nobody is building a real-time AI entity that lives inside the physical classroom**, participates in the lesson with voice, manages turn-taking, privately supports individual students, and feeds the teacher class-wide insights — all at once.

### Why it's defensible
1. **"Co-teacher" is a new category** — not "tutor" (replaces teacher) or "assistant" (helps with prep), but a third entity in the room.
2. **Voice-first + physical presence** — valid in classrooms, unlike screen-based tools.
3. **Whisper architecture is novel** — private audio channels per student while the lesson continues publicly. No product does this.
4. **Cross-student sensing** — "12 of 30 students confused about X right now" has no equivalent.

*(Individual tech components exist in hkathon prototypes; the novelty is the product integration targeting the "AI co-teacher in the room" use case.)*

---

## 2. Market Size

| Market | 2025 | 2030F | CAGR |
|---|---|---|---|
| Global AI in Education | $6.9–7.5B | $41–42.5B | 41–43% |
| Classroom Management Systems | $10.8B | $27.4B | 20.2% |
| India K-12 EdTech | $6.5–7.5B | $29–33B | ~28% |

**India TAM:**
- 260M K-12 students, 1.5M schools, 3.5L+ private schools
- Addressable tech-forward private schools: **50,000–80,000**
- At ₹5,000–15,000/classroom/yr in 10,000 classrooms → **₹5–15 Cr ARR**

---

## 3. Business Model — "Razor-and-Blades SaaS + Hardware Bundle"

**Per-classroom annual SaaS** (hardware optional, bundled):

### India / Global South pricing

| Tier | Price | Contents |
|---|---|---|
| Free (Teacher Basic) | ₹0 | 1 subject, limited sessions, no analytics |
| Teacher Pro | ₹299/mo or ₹2,499/yr | All subjects, unlimited, analytics |
| School Starter | ₹15,000/yr | 5 classrooms, training |
| School Standard | ₹35,000/yr | 15 classrooms, analytics, curriculum alignment |
| School Premium | ₹60,000–1,00,000/yr | Unlimited, API, CSM |
| Hardware bundle | +₹15,000/yr | Mic + speaker kit (like Robyn) |
| Govt / NGO | ₹10–25/student/yr | Bulk, district contracts |

### US / developed markets
- Teacher Plus: $5/mo; School: $30/classroom/yr; District: $2–4/student/yr
- **10x cheaper than Khanmigo district ($35/student/yr) and ChatGPT Edu ($25/teacher/mo)**

### Why this model wins
1. **Inference is nearly free** (Groq ~$0.05–0.90/M tokens → ~$2–30/yr/classroom). 85–95% gross margin.
2. **Hardware = lock-in** (Robyn proves schools pay for hardware+AI bundles).
3. **Per-classroom > per-student** (per-student failed repeatedly in India — Byju's).
4. **Gov contracts are recurring** (3–5 yr renewal cycles).

---

## 4. Go-To-Market Sequence

1. **Months 1–6:** 10–20 "design partner" private schools in Tier 1–2 Indian cities (direct principal outreach, free 3-month pilot).
2. **Months 6–12:** 1–2 state education departments / NGOs (Pratham, Akshara, Azim Premji) via DIKSHA / PM SHRI.
3. **Months 12–24:** 200–500 private schools + 2–3 states.
4. **Months 18–30:** Global South (Sub-Saharan Africa, SEA, LATAM).
5. **Months 24–36:** US Title I schools.

---

## 5. Moats

| Horizon | Moat |
|---|---|
| 0–12 mo | Voice-first physical presence; 10x cheaper inference |
| 1–3 yr | **Curriculum data flywheel** (Indian classroom interaction dataset — no one has it); teacher habit lock-in; Hindi/Tamil/Telugu/Marathi/Bengali voice |
| 3–5 yr | Network effects; gov platform integration (DIKSHA); curriculum intelligence as a service |

---

## 6. Investor One-Pager

> **Sahayak Live** is an AI co-teacher that sits in physical classrooms alongside teachers — managing turn-taking, whispering private help to confused students, detecting live gaps, and generating post-class insights. It's the first product in the "AI co-teacher in the room" category. Market: $41B AI-in-education by 2030. Model: per-classroom SaaS at 85–95% gross margin. Moats: a proprietary dataset of Indian classroom interactions + hardware lock-in. NEP 2020 mandates digital classroom adoption — the tailwind is structural.
