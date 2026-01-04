import pandas as pd
from sqlalchemy import text
from src.config import mysql_engine, BATCH_SIZE
from backend_toolkit.logger import get_logger

logger = get_logger(__name__)

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


def fetch_source_rows(last_id: int, run_id: str) -> pd.DataFrame:
    try:
        with mysql_engine.connect() as conn:
            df = pd.read_sql(
                FETCH_SQL,
                conn,
                params={"last_id": last_id, "limit": BATCH_SIZE},
            )

        logger.debug(
            "fetched source rows completed.",
            extra={"last_tms_id": last_id, "row_count": len(df), "run_id": run_id},
        )
        return df

    except Exception as exc:
        logger.error(
            "failed fetching source rows",
            extra={"last_tms_id": last_id, "error": str(exc), "run_id": run_id},
        )
        raise
