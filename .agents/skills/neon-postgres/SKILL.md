---
name: neon-postgres
description: >-
  Comprehensive guide and best practices for Neon Serverless Postgres, covering connection pooling (-pooler endpoints), asyncpg / SQLAlchemy configuration, pgvector index optimization, branch-first CI/CD migrations, and scale-to-zero tuning.
---

# Neon Serverless Postgres Guide & Best Practices

This skill provides step-by-step procedures, technical specifications, and operational guardrails for integrating and running **Neon Serverless Postgres** in production applications (specifically FastAPI, SQLAlchemy, Alembic, and pgvector).

---

## 1. Connection Types & Endpoints

Neon provisions two compute hostnames for each branch:

### A. Direct Endpoint (Non-Pooled)
* **Format:** `ep-[id].[region].aws.neon.tech:5432/[dbname]`
* **Characteristics:** Direct connection to the Postgres compute engine. Supports full session state, temporary tables, advisory locks, and prepared statements.
* **Primary Use Cases:**
  * Running schema migrations via **Alembic**, Flyway, or Liquibase.
  * Long-running analytics or batch background tasks.
  * Generating initial schema dumps or restoring backups.

### B. Pooled Endpoint (PgBouncer)
* **Format:** `ep-[id]-pooler.[region].aws.neon.tech:5432/[dbname]`
* **Characteristics:** Sits behind managed PgBouncer instances running in **transaction pooling mode**. Automatically queues and reuses connections to prevent exhausting Postgres connection limits during serverless spikes.
* **Primary Use Cases:**
  * High-concurrency web requests (e.g., FastAPI, Next.js API routes).
  * Short-lived stateless queries.

---

## 2. FastAPI + SQLAlchemy + asyncpg Configuration

When using Python's `asyncpg` driver with Neon's `-pooler` endpoint, PgBouncer's transaction pooling mode requires disabling client-side named prepared statements to avoid `prepared statement "_asyncpg_stmt_x" does not exist` errors.

### A. Connection String Adapter
Neon connection strings come formatted as:
```
postgresql://user:password@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
```

For SQLAlchemy `asyncpg`:
```
postgresql+asyncpg://user:password@ep-xyz-pooler.us-east-2.aws.neon.tech/neondb?ssl=require
```

### B. SQLAlchemy Engine Setup
In `backend/app/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine

connect_args = {}

# Detect Neon PgBouncer pooler and disable statement cache
if "-pooler" in settings.DATABASE_URL:
    connect_args["statement_cache_size"] = 0
    connect_args["prepared_statement_cache_size"] = 0

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    connect_args=connect_args,
)
```

---

## 3. Alembic Migrations with Neon

Alembic uses transaction-level DDL locks and version tables.

### Rule: Always run Alembic against the Direct Endpoint (Non-Pooler)
In `backend/alembic.ini` or `backend/app/config.py`:
* Ensure the migration runner connects to `ep-xyz...neon.tech` (without `-pooler`).
* Or programmatically strip `-pooler.` from the host when executing migrations:
  ```python
  migration_url = settings.DATABASE_URL.replace("-pooler.", ".")
  ```

---

## 4. Vector Search & `pgvector` Optimization

Neon provides native support for `pgvector`.

### A. Enable Extension
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### B. Indexing Guidelines for Neon
For PrepPilot interview question similarity and context retrieval:
* **HNSW (Hierarchical Navigable Small World):** Recommended for production. Offers faster queries and better recall, built incrementally in memory.
  ```sql
  CREATE INDEX idx_question_embeddings_hnsw 
  ON questions 
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
  ```
* **IVFFlat:** Requires a training step after data is populated. Re-index once the dataset reaches > 10,000 vectors.

---

## 5. Branch-First CI/CD Workflow

Leverage Neon branching in GitHub Actions or preview pipelines:

```yaml
name: Test Migrations & Branch
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create Neon Branch
        run: |
          BRANCH_URL=$(neon branches create --name pr-${{ github.event.number }} --output json | jq -r .connection_uri)
          echo "DATABASE_URL=$BRANCH_URL" >> $GITHUB_ENV
      - name: Run Alembic Migrations
        run: |
          cd backend && alembic upgrade head
      - name: Run Integration Tests
        run: |
          cd backend && pytest tests/integration
      - name: Clean Up Branch
        if: always()
        run: |
          neon branches delete pr-${{ github.event.number }}
```

---

## 6. Egress & Scale-to-Zero Optimization

1. **Avoid `SELECT *` on Embedding Tables:** Embeddings (e.g., 384 or 1536 float arrays) significantly increase egress payload size. Select only `id`, `title`, and scalar fields during list queries.
2. **Cold Starts:** Scale-to-zero compute turns on in ~300ms upon the first incoming request. For user-facing latency guarantees, add an endpoint health check ping or configure min-compute to `0.25 CU` always-on for production.

