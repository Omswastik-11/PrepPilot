---
name: neon
description: >-
  Overview and operational guide for Neon, a complete set of cloud backend primitives around Lakebase Postgres including instant branching, copy-on-write storage, and autoscaling.
---

# Neon Cloud Backend & Lakebase Postgres Overview

Neon provides a complete suite of serverless cloud backend primitives built around **Lakebase Postgres**, designed with an agent-first and branch-first architecture.

---

## 1. Core Architectural Primitives

### Lakebase Postgres (Disaggregated Compute & Storage)
* **Separation of Compute and Storage:** Compute instances run as stateless containers, while storage is managed by a custom copy-on-write page-level storage engine backed by S3-compatible cloud object storage.
* **Autoscaling:** Computes automatically adjust CPU and memory based on live query load without dropped connections or restarts.
* **Scale-to-Zero:** Computes pause after a configurable period of inactivity (default: 5 minutes), bringing idle compute costs to zero. Cold-start wake-up takes ~300-500ms.

### Copy-on-Write Database Branching
* **Git-like Branching:** Create isolated, fully functional database clones in ~1 second with zero initial storage duplication.
* **Isolated Compute Endpoints:** Each branch has its own hostname and connection credentials, allowing safe experimentation, migration testing, and preview deployments.
* **Time Travel / Point-in-Time Recovery:** Branch from any past transaction timestamp or Log Sequence Number (LSN) within the history retention window.

### S3-Compatible Branching Object Storage
* Managed object storage buckets that branch alongside the database. Modifying or uploading files on a dev branch does not affect production assets.

### Managed Better Auth & Functions
* Integrated session and user management adhering to standard Better Auth schemas.
* Serverless JavaScript/TypeScript handlers running on Node.js directly adjacent to the database with function triggers.

### AI Gateway
* Direct, unified gateway to frontier and open-weight models (Gemini, Claude, Llama) with zero-margin token pricing and managed API keys.

---

## 2. Quick Reference for Developers & Agents

| Feature | Direct Endpoint | Pooled Endpoint |
| :--- | :--- | :--- |
| **Hostname Pattern** | `ep-<name>.<region>.aws.neon.tech` | `ep-<name>-pooler.<region>.aws.neon.tech` |
| **Port** | `5432` | `5432` |
| **Protocol** | Native PostgreSQL (TCP) | PgBouncer (Transaction Pooling) |
| **Best Used For** | Alembic migrations, DDL, long-lived sessions | FastAPI / Next.js web requests, serverless lambdas |
| **SSL Requirement** | Mandatory (`sslmode=require`) | Mandatory (`sslmode=require`) |

---

## 3. Recommended Workflow for PrepPilot

1. **Production:** Connect FastAPI to the `-pooler` endpoint to handle high concurrency and bursty traffic with low connection overhead.
2. **Migrations (Alembic):** Connect Alembic directly to the non-pooler endpoint (or configure transaction-safe locks) to execute schema updates safely.
3. **Branching in CI/CD:** Spin up an ephemeral branch on Pull Requests, run `alembic upgrade head` and integration tests against it, then delete the branch upon merge.

