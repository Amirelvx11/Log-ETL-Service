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

# Required ENV variables
SOURCE_DB = _require_env("SOURCE_DB") # pyodbc SQLAlchemy URI
TARGET_DB = _require_env("TARGET_DB") # pyodbc SQLAlchemy URI
USER_GUID = _require_env("USER_GUID") # MUST be valid in system.User.Id

# Engines (MySQL and MSSQL)
src_engine = create_engine(SOURCE_DB, pool_pre_ping=True)
dst_engine = create_engine(
    TARGET_DB,
    pool_pre_ping=True,
    fast_executemany=True,
    max_overflow=5,
    pool_timeout=5,
    pool_recycle=1800,
    connect_args={"timeout": 5, "LoginTimeout": 5},
)
