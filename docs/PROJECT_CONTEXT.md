# PrepPilot — Project Context

> Last Updated: Phase 2 (August 2026)

## Current Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    PrepPilot Backend                           │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │  Routes      │───▶│  Models      │───▶│  PostgreSQL  │    │
│  │  (HTTP layer)│    │  (ORM layer) │    │  (Database)  │    │
│  └──────┬───────┘    └──────────────┘    └──────────────┘    │
│         │                                                      │
│  ┌──────┴───────┐    ┌──────────────┐                        │
│  │  Middleware   │    │  Utils       │                        │
│  │  (Auth guard) │    │  (Security)  │                        │
│  └──────────────┘    └──────────────┘                        │
│                                                                │
│  Note: Service Layer not yet implemented (Phase 4)            │
│  Currently routes contain some business logic directly        │
└──────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
backend/
├── app/
│   ├── __init__.py              # Package marker
│   ├── config.py                # Pydantic-settings config with fail-fast validation
│   ├── database.py              # Engine, session factory, get_db() dependency
│   ├── main.py                  # FastAPI app, CORS, lifespan, router mounting
│   ├── models/
│   │   ├── __init__.py          # Model registry — imports all models + Base
│   │   ├── base.py              # DeclarativeBase, UUIDMixin, TimestampMixin
│   │   ├── user.py              # User model (UUID PK, guest, role, email)
│   │   ├── interview.py         # Interview model (JSONB metadata, status tracking)
│   │   └── question.py          # Question + Answer models (1:1 relationship)
│   ├── schemas/
│   │   └── user.py              # UserCreate, UserResponse, Token, TokenData
│   ├── routes/
│   │   └── auth.py              # Register, Login, Guest, /me endpoints
│   ├── services/
│   │   └── __init__.py          # Empty — service layer coming in Phase 4
│   ├── middleware/
│   │   └── auth.py              # get_current_user dependency (JWT validation)
│   └── utils/
│       └── security.py          # bcrypt hashing, JWT token creation
├── alembic/
│   ├── env.py                   # Alembic config — imports models from registry
│   └── versions/
│       └── 49c5048f7be3_initial_migration.py
├── tests/                       # Empty — testing coming in Phase 10
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Database Schema

### users
| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK, default uuid4 | Via UUIDMixin |
| email | VARCHAR(255) | UNIQUE, nullable, indexed | Nullable for guests |
| password_hash | VARCHAR(255) | nullable | Nullable for guests |
| name | VARCHAR(100) | nullable | |
| is_guest | BOOLEAN | NOT NULL, default false | |
| role | VARCHAR(20) | NOT NULL, default "user" | Prep for Phase 3 RBAC |
| created_at | TIMESTAMP | NOT NULL, server_default now() | Via TimestampMixin |
| updated_at | TIMESTAMP | NOT NULL, server_default now(), onupdate | Via TimestampMixin |

### interviews
| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | Via UUIDMixin |
| user_id | UUID | FK → users.id, CASCADE, indexed | |
| interview_type | VARCHAR(50) | NOT NULL | dsa, hr, ml, backend, frontend |
| difficulty | VARCHAR(20) | default "medium" | easy, medium, hard |
| status | VARCHAR(20) | default "in_progress" | in_progress, completed, abandoned |
| total_score | FLOAT | nullable | Calculated after completion |
| company | VARCHAR(100) | nullable | |
| started_at | TIMESTAMP | nullable | When interview began |
| completed_at | TIMESTAMP | nullable | When interview finished |
| metadata | JSONB | nullable | Extensible key-value data |
| created_at | TIMESTAMP | NOT NULL, server_default | Via TimestampMixin |
| updated_at | TIMESTAMP | NOT NULL, server_default | Via TimestampMixin |

**Indexes**: `ix_interviews_user_id`, `ix_interviews_user_id_status` (composite)

### questions
| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | Via UUIDMixin |
| interview_id | UUID | FK → interviews.id, CASCADE, indexed | |
| question_text | TEXT | NOT NULL | |
| question_order | INTEGER | NOT NULL | |
| time_limit_seconds | INTEGER | default 120 | |
| ideal_answer | TEXT | nullable | Filled by AI evaluation |
| created_at | TIMESTAMP | NOT NULL | Via TimestampMixin |
| updated_at | TIMESTAMP | NOT NULL | Via TimestampMixin |

**Constraints**: `uq_interview_question_order` UNIQUE(interview_id, question_order)

### answers
| Column | Type | Constraints | Notes |
|--------|------|------------|-------|
| id | UUID | PK | Via UUIDMixin |
| question_id | UUID | FK → questions.id, CASCADE, UNIQUE, indexed | 1:1 with Question |
| user_answer | TEXT | nullable | Null if skipped/timed out |
| time_taken_seconds | INTEGER | nullable | |
| score | FLOAT | nullable | Filled by AI |
| feedback | TEXT | nullable | Filled by AI |
| strengths | TEXT[] | nullable | PostgreSQL ARRAY |
| weaknesses | TEXT[] | nullable | PostgreSQL ARRAY |
| submitted_at | TIMESTAMP | nullable | |
| created_at | TIMESTAMP | NOT NULL | Via TimestampMixin |
| updated_at | TIMESTAMP | NOT NULL | Via TimestampMixin |

## APIs

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/auth/register | No | Register new user |
| POST | /api/auth/login | No | Login, returns JWT |
| POST | /api/auth/guest | No | Create guest session |
| GET | /api/auth/me | Yes | Get current user profile |
| GET | / | No | Health check |
| GET | /health | No | Detailed health check |

## Features Implemented
- User registration with email/password (bcrypt hashed)
- JWT authentication (HS256, 24-hour expiry)
- Guest user support (no registration required)
- Protected routes via get_current_user dependency
- PostgreSQL with async SQLAlchemy 2.0
- Connection pooling (5 connections, 10 overflow)
- Alembic migrations
- Docker + Docker Compose

## Design Decisions
See `docs/DECISIONS.md` for the full ADR log.

## Tech Stack
- **Runtime**: Python 3.12
- **Framework**: FastAPI 0.115
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 16
- **Migrations**: Alembic 1.13
- **Auth**: python-jose (JWT) + passlib (bcrypt)
- **Config**: pydantic-settings
- **Container**: Docker + Docker Compose
- **AI** (planned): Google Gemini via google-genai

## Dependencies
See `backend/requirements.txt` for full list.

## Security
- Passwords hashed with bcrypt (passlib)
- JWT tokens with HS256 signing
- UUID primary keys prevent ID enumeration
- Generic error messages prevent user enumeration on login
- CORS configured for localhost:3000 (frontend)
- CASCADE deletes prevent orphan records

## Current Progress
- [x] Phase 0: Project Vision & Architecture
- [x] Phase 1: FastAPI Fundamentals, Config, DI Basics
- [x] Phase 2: SQLAlchemy ORM, Database Sessions, Migrations
- [ ] Phase 3: Authentication, JWT, RBAC
- [ ] Phase 4: Clean Architecture (Repository, Service, DTOs)
- [ ] Phase 5–13: See ROADMAP.md

## Pending Work
- Service Layer (business logic in routes currently)
- Repository Pattern (raw SQLAlchemy in routes)
- Interview domain routes
- AI integration
- Redis/caching
- Testing
- CI/CD
- Deployment

## Known Technical Debt
1. **Business logic in routes**: `routes/auth.py` directly queries SQLAlchemy models. Should go through a Service → Repository chain (Phase 4)
2. **No refresh tokens**: Current JWT has 24-hour expiry with no refresh mechanism (Phase 3)
3. **No RBAC enforcement**: `role` column exists but no authorization middleware (Phase 3)
4. **Health check is fake**: `/health` returns `"database": "connected"` without actually checking (Phase 9)
5. **No input sanitization beyond Pydantic**: Relies entirely on Pydantic validation (Phase 9)

## Next Phase
Phase 3: Authentication — Password Hashing deep dive, JWT mechanics, Refresh Tokens, Authorization, Role-Based Access Control
