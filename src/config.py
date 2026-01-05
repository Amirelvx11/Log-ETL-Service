import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required env var: {key}")
    return value

# REQUIRED ENV 
SOURCE_DB = _require_env("SOURCE_DB")
TARGET_DB = _require_env("TARGET_DB")
USER_GUID = _require_env("USER_GUID")

# OPTIONAL (ensure that no limitation based on mssql and your RAM for insert)
BATCH_SIZE = min(int(os.getenv("BATCH_SIZE", "10000")), 50_000)

# Engines (MySQL-source and MSSQL-target)
mysql_engine = create_engine(
    SOURCE_DB,
    pool_pre_ping=True,
    pool_recycle=3600,
)
mssql_engine = create_engine(
    TARGET_DB,
    pool_pre_ping=True,
    fast_executemany=True,
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=3600,
    isolation_level="READ COMMITTED",
)


PART_ID_BY_PREFIX = {
    "AF70": "A3925DD2-F7C3-4E27-B487-E547F8F980E2",
    "AF75": "B159B8DA-AD61-4C25-97C8-C82CF7955D06",
}

COMM_MODE_MAP = {
    "4G": 0,
    "GPRS": 1,
    "WIFI": 2,
}

REQUEST_TYPE_MAP = {
    "RUA": 0,
    "RAL": 1,
}
