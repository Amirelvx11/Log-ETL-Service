from backend_toolkit.monitoring.run_tracker import RunTracker
from backend_toolkit.logger import get_logger
from src.fetch import fetch_source_rows
from src.transform import transform_rows
from src.insert import insert_rows, get_last_inserted_tms_id
from src.config import USER_GUID

logger = get_logger(__name__)

def run_etl():
    with RunTracker("device-log-etl") as run:
        try:
            last_id = get_last_inserted_tms_id()
            logger.info("log-etl started", extra={"last_tms_id": last_id})

            total_inserted = 0

            while True:
                df = fetch_source_rows(last_id)
                if df.empty:
                    break

                transformed = transform_rows(df, USER_GUID)
                inserted = insert_rows(transformed)

                total_inserted += inserted
                last_id = int(df["id"].max())

                logger.info(
                    "batch completed",
                    extra={
                        "after_tms_id": last_id,
                        "batch_inserted": inserted,
                    },
                )

            logger.info(
                "log-etl finished",
                extra={
                    "final_tms_id": last_id,
                    "total_inserted": total_inserted,
                },
            )

        except Exception as exc:
            logger.error(
                "log-etl crashed",
                extra={"error": str(exc), "run_id": run.run_id},
            )
            raise
      

if __name__ == "__main__":
    run_etl()
