"""
Database Connection & Session Management.

SYSTEM DESIGN CONCEPTS IN THIS FILE:
  1. Connection Pooling — We don't create a new DB connection per request.
     Instead, SQLAlchemy maintains a "pool" of connections that get reused.
     This is critical for performance (connecting to DB is expensive ~50ms).

  2. Session Pattern — Each request gets its own "session" (a unit of work).
     The session tracks changes and commits/rolls back as a single transaction.
     This ensures data consistency (either ALL changes save, or NONE do).

  3. Dependency Injection — FastAPI's `Depends()` injects a DB session into
     each route handler. The handler doesn't know or care HOW the session
     is created — it just uses it. This makes testing easy (swap real DB
     for test DB).

  4. Async I/O — We use async SQLAlchemy (`create_async_engine`) because
     database queries are I/O-bound. While waiting for a query response,
     the server can handle other requests. This is how FastAPI achieves
     high concurrency without threads.

INTERVIEW QUESTION: "Why use connection pooling?"
  → Creating a DB connection requires TCP handshake + authentication + SSL.
  → With pooling, you create N connections at startup and reuse them.
  → Default pool size is 5 connections (good for small apps).
  → In production, you'd tune this based on expected concurrent users.

PHASE 2 CHANGE — WHY WE REMOVED AUTO-COMMIT FROM get_db():
  The previous version auto-committed on success and rolled back on error.
  This is "implicit transaction management" — the session dependency decides
  when to commit, not the code that actually knows whether it modified data.

  Problems with auto-commit:
    1. Read-only routes (GET /api/auth/me) trigger an unnecessary COMMIT
    2. Multi-step operations can't be composed into a single transaction
    3. It's "magic" — new team members don't see where the commit happens

  The new version just provides a session and cleans up. The calling code
  (route handler or service layer) decides when to commit. This follows
  the "explicit is better than implicit" principle.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import get_settings
from app.models.base import Base  # Base now lives in models/base.py

settings = get_settings()

# Create the async engine with connection pooling
# pool_size=5: Keep 5 connections ready at all times
# max_overflow=10: Allow up to 10 extra connections during traffic spikes
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in development (set False in prod)
    pool_size=5,
    max_overflow=10,
)

# Session factory — creates new sessions for each request
# expire_on_commit=False: Don't expire objects after commit (avoids lazy loading issues)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session per request.

    Usage in route handlers:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...

    IMPORTANT — Session Lifecycle:
      1. A new session is created when the request starts
      2. The route handler uses the session (queries, inserts, updates)
      3. The route handler calls `await db.commit()` if it modified data
      4. If an exception occurs, the session is rolled back automatically
      5. The session is closed when the request ends

    The route handler is RESPONSIBLE for calling commit(). This is
    deliberate — only the code that knows it modified data should commit.
    Read-only routes never call commit(), which is cleaner and slightly
    more efficient.
    """
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
