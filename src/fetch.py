import pandas as pd
from sqlalchemy import text
from src.config import mysql_engine, BATCH_SIZE

FETCH_SQL = text("""
SELECT
    id,
    serial,
    terminal,
    terminal_number,
    electricity,
    commode,
    base_station,
    start_time,
    vs_device_version,
    vc_device_version,
    cos_device_version,
    request_subject
FROM en_tms.szaf_request_log
WHERE id > :last_id
ORDER BY id ASC
LIMIT :limit
""")


def fetch_source_rows(last_id: int) -> pd.DataFrame:
        with mysql_engine.connect() as conn:
            return pd.read_sql(
                FETCH_SQL,
                conn,
                params={"last_id": last_id, "limit": BATCH_SIZE},
            )

    