"""
Alembic Environment Configuration.

ENGINEERING CONTEXT:
  This file tells Alembic how to connect to the database and what models
  to track. Alembic compares your SQLAlchemy models (Python code) against
  the actual database schema and generates migration scripts for any
  differences.

  KEY CHANGES (PHASE 2):
    - Import Base and all models from app.models (the model registry)
      instead of importing each model individually
    - This means adding a new model only requires updating models/__init__.py,
      not this file
"""

import asyncio
from logging.config import fileConfig
import sys
import os

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from alembic import context
from app.config import get_settings

# Import Base and ALL models from the model registry
# This single import ensures Alembic discovers every model
from app.models import Base

settings = get_settings()

config = context.config

# Override sqlalchemy.url in alembic.ini with the one from our settings
# Direct connection is required for DDL migrations (bypassing PgBouncer pooler if present)
db_url = settings.DATABASE_URL.replace("-pooler.", ".")
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
