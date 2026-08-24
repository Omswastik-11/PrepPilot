# PrepPilot — Architecture Decision Records (ADR)

---

## ADR-001: SQLAlchemy ORM over Raw SQL

**Decision**: Use SQLAlchemy 2.0 ORM with async support

**Alternatives Considered**:
1. Raw asyncpg queries
2. Tortoise ORM (async-native)
3. SQLModel (Pydantic + SQLAlchemy hybrid)

**Pros**:
- SQL injection impossible (parameterized queries)
- Database-agnostic (can switch from PostgreSQL to MySQL with config change)
- Relationships auto-resolved (no manual JOINs)
- Alembic integration for auto-generated migrations
- Industry standard — widely used in production (Stripe, Reddit)

**Cons**:
- 5-15% performance overhead from object mapping
- Steeper learning curve than raw SQL
- Complex queries can be harder to express than raw SQL

**Reason For Choosing**: Safety, migration support, and relationship handling vastly outweigh the marginal performance cost at our scale. The learning investment in SQLAlchemy transfers to any Python backend role.

---

## ADR-002: UUID Primary Keys over Auto-Increment Integers

**Decision**: Use UUID v4 for all primary keys

**Alternatives Considered**:
1. Auto-increment integer (SERIAL/BIGSERIAL)
2. UUID v7 (time-ordered)
3. ULID (Universally Unique Lexicographically Sortable Identifier)

**Pros**:
- Prevents ID enumeration attacks (/users/1 → /users/2)
- Client-side generation without server coordination
- Safe for distributed systems and database merges
- No information leakage about record count or creation order

**Cons**:
- 16 bytes vs 4 bytes storage per key
- Random insertion degrades B-tree index locality
- Longer URLs, harder to debug visually

**Reason For Choosing**: Security (no enumeration) and distributed compatibility are essential for a production system. The storage and index cost is negligible at our scale (thousands of rows, not billions).

---

## ADR-003: Explicit Commit over Auto-Commit in Session Dependency

**Decision**: `get_db()` yields a session without auto-committing. Callers must explicitly commit.

**Alternatives Considered**:
1. Auto-commit on success, rollback on error (previous implementation)
2. Commit in a middleware layer
3. Service-layer transaction decorator

**Pros**:
- Read-only routes don't trigger unnecessary COMMIT
- Transaction boundaries are visible in the calling code
- Multi-step operations can be composed into a single transaction
- Follows "explicit is better than implicit" (PEP 20)

**Cons**:
- More verbose — every write route needs `await db.commit()`
- Forgetting to commit is a silent bug (data appears saved but isn't)

**Reason For Choosing**: Explicitness outweighs verbosity. In production, understanding where commits happen is critical for debugging transaction issues. The Phase 4 Service Layer will centralize commit logic.

---

## ADR-004: lazy="raise" as Default Relationship Loading Strategy

**Decision**: All relationships use `lazy="raise"` by default

**Alternatives Considered**:
1. `lazy="selectin"` (eager load with IN query)
2. `lazy="joined"` (eager load with JOIN)
3. `lazy="select"` (lazy load on access)
4. `lazy="subquery"` (eager load with subquery)

**Pros**:
- Prevents accidental N+1 queries entirely
- Forces developers to explicitly choose loading strategy per query
- Makes the number of SQL queries per endpoint predictable and auditable
- Best practice recommended by SQLAlchemy maintainers for async

**Cons**:
- More verbose — must use `selectinload()` or `joinedload()` explicitly
- Accessing an unloaded relationship raises an error instead of silently loading

**Reason For Choosing**: In async SQLAlchemy, lazy loading doesn't work (can't do synchronous I/O). `lazy="raise"` makes this explicit instead of producing confusing `MissingGreenlet` errors. It also prevents the N+1 problem by design.

---

## ADR-005: Mixins (UUIDMixin + TimestampMixin) over Base Class Inheritance

**Decision**: Use Python mixins for shared model fields (id, created_at, updated_at)

**Alternatives Considered**:
1. Single `BaseModel` class with all shared fields
2. Duplicating fields in each model
3. Abstract base class with `__abstract__ = True`

**Pros**:
- Composition over inheritance — models pick and choose what they need
- TimestampMixin can be used on tables that don't use UUID PKs (if needed later)
- Clean separation of concerns (identity vs auditing)
- Easy to add new mixins (e.g., SoftDeleteMixin) without modifying existing ones

**Cons**:
- Multiple inheritance can be confusing
- MRO (Method Resolution Order) issues if mixins have conflicting attributes

**Reason For Choosing**: Flexibility. A model that doesn't need timestamps (hypothetical: a lookup/enum table) can skip TimestampMixin without losing UUID support. This is the pattern used by Flask-SQLAlchemy and Django's abstract models.

---

## ADR-006: Forward-Looking Role Column on User Model

**Decision**: Add `role` column (default "user") in Phase 2, even though RBAC isn't implemented until Phase 3

**Alternatives Considered**:
1. Add role column in Phase 3 when RBAC is built
2. Use a separate roles/permissions table from the start
3. Store roles in JWT claims only (no database column)

**Pros**:
- Zero migration complexity in Phase 3 (column already exists)
- All existing users automatically have `role="user"` via server_default
- No data backfill needed
- The migration is trivial now (empty or near-empty database)

**Cons**:
- The column sits unused until Phase 3
- Slightly violates YAGNI (You Aren't Gonna Need It) — but we know we will need it

**Reason For Choosing**: Schema evolution is cheapest when the database is small. Adding a column with a default to a table with millions of rows requires an `ALTER TABLE` that can lock the table. Doing it now, with a handful of test rows, is free.

---

## ADR-007: Both server_default and Python default for Timestamps

**Decision**: Use both `default=func.now()` and `server_default=func.now()` on timestamp columns

**Alternatives Considered**:
1. Python `default=datetime.utcnow` only
2. `server_default=func.now()` only
3. PostgreSQL trigger for updated_at

**Pros**:
- Python default works for ORM inserts (most common path)
- Server default works for raw SQL, Alembic data migrations, admin panels
- Defense in depth — timestamps are never missing regardless of insertion method
- `datetime.utcnow` is deprecated in Python 3.12+; `func.now()` is database-native

**Cons**:
- Slightly redundant (two defaults for the same purpose)
- `onupdate` for updated_at only works through ORM, not raw SQL (would need a PostgreSQL trigger for full coverage)

**Reason For Choosing**: The cost of having both is zero. The cost of missing a timestamp (no created_at on a record inserted via raw SQL) is debugging pain. Always choose the defensive option.

---

## ADR-008: External API Calls Outside Database Transactions

**Decision**: Keep all external API calls (e.g., LLM generation, embedding models) strictly *outside* of active database transactions.

**Alternatives Considered**:
1. Performing external API calls while holding the database transaction (e.g., calling Gemini in the middle of a `db.commit()` block or right after a `db.add()`).
2. Managing partial rollbacks manually with SAVEPOINTs.

**Pros**:
- Database connections are held for milliseconds instead of seconds, dramatically improving connection pool utilization and concurrency.
- Prevents transaction timeouts caused by LLM latency (which can spike).
- Ensures that if an AI call fails, no stranded or incomplete data remains in the database.

**Cons**:
- Service layer methods become slightly more complex (requiring a "resolve" phase and an "apply/persist" phase).

**Reason For Choosing**: In a high-latency AI application, holding a database connection while waiting for an LLM to generate text or embeddings is a critical scalability bottleneck. Segregating these operations ensures the database is only accessed when data is fully ready to be written.
