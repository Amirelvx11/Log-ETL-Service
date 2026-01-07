import pandas as pd
from sqlalchemy import text
from src.config import mssql_engine
from backend_toolkit.logger import get_logger

logger = get_logger("insert")


def insert_rows(df: pd.DataFrame, run_id: str) -> int:
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

        logger.info("rows inserted", extra={"row_count": len(df), "run_id": run_id})
        return len(df)

    except Exception as exc:
        logger.error(
            "insert failed",
            extra={"row_count": len(df), "error": str(exc), "run_id": run_id},
        )
        raise


def get_last_inserted_tms_id(run_id: str) -> int:
    try:
        with mssql_engine.connect() as conn:
            last_id = int(
                conn.execute(
                    text("SELECT ISNULL(MAX(TmsLogId),0) FROM Hamon.mfu.DeviceLog")
                ).scalar_one()
            )

        logger.debug("last inserted tms id loaded", extra={"last_tms_id": last_id, "run_id": run_id})
        return last_id

    except Exception as exc:
        logger.error(
            "failed to getting last tms_log_id",
            extra={"error": str(exc), "run_id": run_id},
        )
        raise
    