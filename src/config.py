import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def _require_env(key: str) -> str:
    """Ensure required environment variables are present."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required env var: {key}")
    return value

# REQUIRED ENV 
SOURCE_DB = _require_env("SOURCE_DB")   # SQLAlchemy URI (MySQL)
TARGET_DB = _require_env("TARGET_DB")   # SQLAlchemy URI (MSSQL)
USER_GUID = _require_env("USER_GUID")   # MUST exist in system.User.Id
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "2000")) #ensure no limitation based on mssql insert

# Engines (MySQL-source and MSSQL-target)
mysql_engine = create_engine(SOURCE_DB, pool_pre_ping=True)
mssql_engine = create_engine(
    TARGET_DB,
    pool_pre_ping=True,
    fast_executemany=True,
    max_overflow=5,
    pool_timeout=5,
    pool_recycle=1800,
    connect_args={"timeout": 5, "LoginTimeout": 5},
)
