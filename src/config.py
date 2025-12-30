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
    max_overflow=5,
    pool_timeout=5,
    pool_recycle=1800,
    connect_args={"timeout": 5, "LoginTimeout": 5},
)

PART_ID_BY_PREFIX = {
    "AF70": "A3925DD2-F7C3-4E27-B487-E547F8F980E2",
    "AF75": "B159B8DA-AD61-4C25-97C8-C82CF7955D06",
}

COMM_MODE_MAP = {
    0: 4,
    1: 1,
    2: 2,
}

REQUEST_TYPE_MAP = {
    "RUA": 0,
    "RAL": 1,
}