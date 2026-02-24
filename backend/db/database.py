from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool

from config import DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW

Base = declarative_base()

# SQLite: StaticPool, check_same_thread=False
# PostgreSQL: QueuePool with connection pool settings
is_sqlite = "sqlite" in DATABASE_URL
connect_args = {"check_same_thread": False} if is_sqlite else {}
pool_class = StaticPool if is_sqlite else QueuePool
pool_size = {} if is_sqlite else {"pool_size": DB_POOL_SIZE, "max_overflow": DB_MAX_OVERFLOW}

# Supabase and cloud DBs require SSL
if not is_sqlite and "sslmode" not in DATABASE_URL:
    if "supabase" in DATABASE_URL or "neon" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL + ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    poolclass=pool_class,
    **pool_size,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    from . import models  # noqa: F401 - ensure models are registered
    Base.metadata.create_all(bind=engine)

    # Verify schema matches models
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users'"))
        columns = [row[0] for row in result]
        print(f"[DB CHECK] users table columns: {columns}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
