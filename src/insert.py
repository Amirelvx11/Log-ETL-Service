import pandas as pd
from sqlalchemy import text
from src.config import mssql_engine
from backend_toolkit.logger import get_logger

logger = get_logger(__name__)


def insert_rows(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    try:
        with mssql_engine.begin() as conn:
            df.to_sql(
                name="DeviceLog",
                schema="mfu",
                con=conn,
                if_exists="append",
                index=False,
                chunksize=500,
                method=None,
            )

        logger.info("rows inserted", extra={"row_count": len(df)})
        return len(df)

    except Exception as exc:
        logger.error(
            "insert failed",
            extra={"row_count": len(df), "error": str(exc)},
        )
        raise


def get_last_inserted_tms_id() -> int:
    try:
        with mssql_engine.connect() as conn:
            last_id = int(
                conn.execute(
                    text("SELECT ISNULL(MAX(TmsLogId),0) FROM Hamon.mfu.DeviceLog")
                ).scalar_one()
            )

        logger.info("last inserted tms id loaded", extra={"last_tms_id": last_id})
        return last_id

    except Exception as exc:
        logger.error(
            "failed to getting last tms_log_id",
            extra={"error": str(exc)},
        )
        raise
    