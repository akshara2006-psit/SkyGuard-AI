from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from ..config import settings
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)
db_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
os.makedirs(db_dir, exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def _get_sqlite_db_path() -> str:
    """Extract the file path from the DATABASE_URL for direct sqlite3 access."""
    url = settings.DATABASE_URL
    # Handles: sqlite+aiosqlite:///./database/skyguard.db  or  sqlite:///./database/skyguard.db
    for prefix in ("sqlite+aiosqlite:///", "sqlite:///"):
        if url.startswith(prefix):
            path = url[len(prefix):]
            # Resolve relative paths against the database/ directory created above
            if not os.path.isabs(path):
                path = os.path.join(db_dir, os.path.basename(path))
            return os.path.normpath(path)
    return url  # fallback, will fail gracefully if not sqlite

def migrate_sqlite_schema() -> None:
    """
    Idempotent SQLite schema migration.

    Checks PRAGMA table_info for every table listed in REQUIRED_MIGRATIONS
    and issues ALTER TABLE ... ADD COLUMN for any column that is present in
    the migration spec but absent from the physical table.

    Safe to call on every startup:
      - Never drops or modifies existing columns.
      - Never deletes rows.
      - Never recreates the database.
      - Skips any column that already exists.
    """
    if "sqlite" not in settings.DATABASE_URL:
        logger.info("Database schema migration: non-SQLite backend detected, skipping column migration.")
        return

    # Columns to guarantee exist in sensor_health table.
    # Format: (column_name, column_definition_for_ALTER_TABLE)
    REQUIRED_MIGRATIONS: dict[str, list[tuple[str, str]]] = {
        "sensor_health": [
            ("degradation_trend",          "VARCHAR DEFAULT 'STABLE'"),
            ("maintenance_status",         "VARCHAR DEFAULT 'NOMINAL_MONITORING'"),
            ("maintenance_recommendation", "TEXT"),
            ("maintenance_reasons",        "TEXT"),
        ]
    }

    db_path = _get_sqlite_db_path()
    logger.info("Checking database schema migrations...")
    print("Checking database schema migrations...")

    changes_made = False
    try:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            for table_name, columns in REQUIRED_MIGRATIONS.items():
                # Check the table exists at all
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                if cur.fetchone() is None:
                    logger.warning(
                        "Schema migration: table '%s' does not exist yet; skipping.", table_name
                    )
                    continue

                # Read existing columns via PRAGMA
                cur.execute(f"PRAGMA table_info({table_name})")
                existing_columns = {row[1].lower() for row in cur.fetchall()}

                for col_name, col_def in columns:
                    if col_name.lower() not in existing_columns:
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"
                        cur.execute(alter_sql)
                        conn.commit()
                        msg = f"Added missing column: {table_name}.{col_name}"
                        logger.info(msg)
                        print(msg)
                        changes_made = True
        finally:
            conn.close()
    except Exception as exc:
        logger.error("Schema migration failed: %s", exc, exc_info=True)
        raise

    if changes_made:
        print("Database schema migration completed")
        logger.info("Database schema migration completed")
    else:
        print("Database schema migration completed - no changes required")
        logger.info("Database schema migration completed - no changes required")

async def init_db():
    from ..models.db_models import Station, SensorReading, Anomaly, SensorHealth, Alert
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Run idempotent column migrations for pre-existing tables
    migrate_sqlite_schema()

async def close_db():
    await engine.dispose()

