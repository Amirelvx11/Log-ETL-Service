import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.config import mysql_engine, mssql_engine, BATCH_SIZE

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
    try:
        with mysql_engine.connect() as conn:
            df = pd.read_sql(
                FETCH_SQL,
                conn,
                params={"last_id": last_id, "limit": BATCH_SIZE},
            )

        if not df.empty:
            print(
                f"[fetch] rows={len(df)} "
                f"id_min={df['id'].min()} "
                f"id_max={df['id'].max()}"
            )
            assert df["id"].is_monotonic_increasing, "[fetch] id order broken"

        return df
    
    except SQLAlchemyError as e:
        print(f"[fetch_batch] error: {e}")
        return pd.DataFrame()
    
    
def get_last_tms_log_id() -> int:
    sql = text(
        "SELECT ISNULL(MAX(TmsLogId), 0) FROM Hamon.mfu.DeviceLog WITH (NOLOCK)"
    )

    try:
        with mssql_engine.connect() as conn:
            return int(conn.execute(sql).scalar_one())
    except SQLAlchemyError as e:
        print(f"[get_last_tms_log_id] error: {e}")
        return 0
    