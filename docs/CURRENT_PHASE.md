# PrepPilot — Current Phase & Master Architecture Status

**Last Updated:** September 2026  
**Current Phase:** Transitioning from **Phase A (Hardening & Bug Fixes)** to **Phase B (Resume Profiles, Candidate Memory & Company Intelligence)**

---

## 1. Executive Product Vision (Core Story)

PrepPilot is **NOT** just an AI chatbot that asks questions. The core differentiator and product story is:

```text
    EVALUATE (AI Answer Scoring & Feedback)
       ↓
    REMEMBER (Candidate Memory Extraction & Embedding in pgvector)
       ↓
    RETRIEVE (Hybrid pgvector Search across Memories & Question Bank)
       ↓
     ADAPT   (Dynamic Difficulty & Topic Progression across Sessions)
```

The system remembers the candidate across interview sessions, retrieves relevant candidate knowledge and interview knowledge, evaluates answers, and uses those signals to adapt future questions.

---

## 2. Current Codebase Status

### Frontend (`frontend/src`):
- **Stack:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Lucide Icons, Zustand.
- **Implemented & Verified:**
  - JWT / localStorage authentication (`/login`, `/register`).
  - Sidebar with recent interview history (`/api/interviews?limit=10`).
  - Interview creation dashboard (`/`) with interview type, difficulty, question count, and company.
  - Dynamic conversational chat interface (`/interviews/[id]`) with active question detection, timer tracking, and answer submission.
  - Visual AI evaluation cards (Score/10, Feedback, Strengths, Areas to Improve).
  - Interview completion screen.

### Backend (`backend/app`):
- **Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (asyncio), PostgreSQL 16 with `pgvector`, Alembic, Google Gemini API (`google-genai`), HuggingFace Inference API fallback.
- **Implemented & Verified:**
  - Clean Architecture (routes → services → repositories → models).
  - Auth routes: `/register`, `/login`, `/refresh`, `/logout`, `/me`, `/guest` with bcrypt hashing and stateless JWTs.
  - Multi-provider AI orchestrator: primary Google Gemini (`gemini-3.6-flash`) with automatic fallback to HuggingFace (`Mistral-7B-Instruct-v0.2`).
  - Interview lifecycle: `/api/interviews`, `/api/interviews/{id}`, submit answer, abandon, complete.
  - Candidate service & pgvector memory extraction.
  - QuestionBank and KnowledgeSource models with embedding storage.

### Recent Hardening & Fixes (Phase 0 & A Completed):
1. **Adaptive Difficulty Logic:**
   - Fixed 0–10 score scale comparison in `InterviewPlanner` (`>= 8.0` promotes, `< 5.0` demotes, `5.0–7.9` stays stable).
   - Fixed difficulty vocabulary mapping (`easy/medium/hard` ↔ `Junior/Mid/Senior/Principal`).
   - Fixed initial difficulty inheritance so Question 1 reflects the user's selected difficulty.
2. **Security & BOLA Hardening:**
   - Bound all candidate routes (`/api/candidate/*`) to `current_user: User = Depends(get_current_user)`.
   - Enforced authorization guards (`_ensure_access`) preventing unauthorized cross-user profile/memory access.
3. **pgvector Indexing:**
   - Added Alembic migration for HNSW vector indexes (`vector_cosine_ops`) on `question_bank.embedding` and `candidate_memories.embedding`.
4. **Stop the Bleeding (Phase 0):**
   - Web research pipeline now properly extracts text with BeautifulSoup and generates context-aware questions.
   - Fully transitioned to Alembic schema ownership (removed `create_all` from startup).
   - `/health` endpoint correctly executes a real DB query to verify connectivity.
   - API CORS allowed origins are now environment-driven.
   - Implemented fail-fast initialization in AI services when `GEMINI_API_KEY` is missing.
5. **Resume Management (Phase B):**
   - Added PDF/DOCX text extraction utilities (`pdfplumber` and `python-docx`).
   - Created `/api/candidate/documents` endpoint for resume uploads.
   - Fixed `DocumentService` parsing bugs by migrating to Gemini's `GenerateContentConfig` with strict `response_schema`.
   - Wired extracted resume background (experience years, target roles, memories) into `InterviewPlanner` and `AIService` prompts.
   - Built rich Candidate Profile frontend page (`/profile`) with resume upload, parsed skills visualization, and dynamic glassmorphism design.
6. **Test Suite Status:** 65 unit & security tests passing cleanly in `backend/tests`.

---

## 3. Remaining Roadmap (Based on Final MVP Plan)

**🎉 ALL MVP PILLARS COMPLETED & VERIFIED 🎉**

### Pillar 1: Resume Profiles & Candidate Knowledge Ingestion (COMPLETED)
- **Resume Profile Architecture:** Supports role-targeted resumes.
- **Storage Strategy:** Stores metadata, target role, and parsed facts in PostgreSQL.
- **Upload API:** `POST /api/candidate/documents` accepts PDF/DOCX using `pdfplumber` and Gemini structured extraction (`skills`, `experience_years`, `memories`).
- **Frontend Integration:** Candidate Profile / Resume view in Next.js.

### Pillar 2: Company-Aware Question Retrieval & Role Selection (COMPLETED)
- **Company Field Propagation:** Selected company actively biases question selection.
- **Role Selection:** Candidates can explicitly select a Target Role before starting an interview.
- **Question Bank Ingestion:** Web scraping pipeline `knowledge_service.py` ingests company-tagged questions.
- **Hybrid Retrieval:** Match by `domain` + `difficulty` + `company` + `role` via pgvector cosine similarity.

### Pillar 3: Dashboard & Historical Performance Analytics (COMPLETED)
- **Analytics Endpoint:** `GET /api/candidate/analytics` aggregating total interviews, scores, and activity heatmap.
- **Live Strengths/Weaknesses:** Synthesizes granular candidate memories into high-level themes upon interview completion.
- **Frontend Dashboard:** Rich analytical view with charts, scores, and readiness indicators (`Heatmap.tsx`).

### Pillar 4: Production Deployment Readiness (READY)
- **Frontend:** Ready for Vercel.
- **Backend:** Ready for Render / Railway Dockerized FastAPI.
- **Database:** Postgres URL parameterized for Supabase `pgvector`.
- **Security Check:** Zero secrets committed, CORS environment-driven, `create_all()` removed in favor of Alembic.

---

## 4. Next Phase: UI Polish & Demo Features (See `enhancement_handoff.md`)
- Adding Framer Motion animations to chat
- Implementing Google OAuth2 Sign-In
- Adding Score Trend Sparklines
- Displaying Ideal Answer toggles
- Expanded settings (Theme toggle, defaults)

---

## 5. Architectural Rules for Development

1. **Do NOT rewrite working architecture:** Preserve existing Next.js App Router, FastAPI async patterns, and Zustand store.
2. **Shift-Left AI Calls:** Run external LLM and embedding calls *before* or *outside* database transactions to prevent connection pool starvation.
3. **No Fake / Hardcoded AI:** Always use real Gemini with HuggingFace fallback.
4. **Authoritative Backend:** The backend is the single source of truth for interview state, question progression, and evaluations.
5. **Privacy by Design:** Candidate resumes and memories are private—never expose unauthenticated endpoints or leak cross-tenant data.
