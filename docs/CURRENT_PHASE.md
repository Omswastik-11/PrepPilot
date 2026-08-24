# PrepPilot — Current Phase

## Current Phase
**Phase 7: Hardening Pass — Adaptive Interviewer & Architecture Fixes**

## Learning Objectives
1. **Transaction Hygiene**: Understanding how long-running network calls (like LLM API calls or vector embeddings) should NOT be kept inside active database transactions, to avoid holding locks and consuming connection pool resources.
2. **Idempotency & Data Provenance**: Designing systems that can safely retry data ingestion (like URL ingestion for question generation) without duplicating data, and tracking the `status` of generated data before making it live (`pending_review`).
3. **Vector Similarity (pgvector)**: Using L2 distance (`<->` or `.l2_distance()`) in SQLAlchemy to find semantically similar candidate memories rather than relying on basic substring matching.
4. **RBAC in FastAPI**: Implementing simple dependency-based authorization (`require_role("admin")`) to secure sensitive endpoints (Knowledge Base ingestion).

## Concepts Learned
- **Alembic Constraints & Defaults**: Adding `UniqueConstraint` and `server_default` dynamically to existing tables via Alembic to guarantee data integrity at the lowest level.
- **Service Layer Segregation**: Splitting "Resolution" (getting the data ready and figuring out what to insert/update) from "Application" (the actual DB write) inside a Service method. This allows `InterviewService` to resolve memory upserts using AI *before* opening its transaction.

## Files Modified
- `app/routes/knowledge.py` — Auth-protected with `require_role`.
- `app/models/knowledge.py` — Added `status` to `KnowledgeSource` and `QuestionBank`.
- `alembic/versions/..._add_knowledge_status.py` — Auto-generated migration.
- `app/repositories/knowledge_repository.py` — Implemented `get_by_reference` for idempotent upserts.
- `app/services/retrieval_service.py` — Filtered retrieved questions by `status == 'accepted'`.
- `app/config.py` — Added `MEMORY_DEDUP_THRESHOLD`.
- `app/repositories/candidate_repository.py` — Implemented L2 distance search for memory dedup.
- `app/services/candidate_service.py` — Refactored `upsert_memory` into resolution and application steps.
- `app/services/interview_service.py` — Shifted LLM and embedding calls out of the `submit_answer` transaction; fixed literal `\n` bug.
- `app/services/knowledge_service.py` — Fixed literal `\n` bug.
- `tests/api/test_interviews.py` — Added test for AI planning failure transaction rollback.
- `tests/api/test_knowledge.py` — Added auth protection tests.
- `tests/unit/test_candidate_service.py` — Updated mock assertions for the new embedding-first logic.

## Architecture Decisions
1. **Shift-Left AI Calls**: Moved all AI evaluations and embedding generations outside the core `submit_answer` database transaction. If the AI fails, the DB remains clean and connections aren't hogged.
2. **Default `pending_review`**: Automated ingestion shouldn't poison the live question bank. By defaulting to `pending_review` and strictly filtering in `RetrievalService`, humans can curate AI outputs.
3. **Embedding-Based Dedup**: Replaced naive substring matching with semantic vector similarity for Candidate Memories to properly deduplicate concepts (e.g., "Good at Python" vs "Strong Python skills").

## Next Session
Phase 8: Frontend Integration (or whichever feature comes next)!
