from backend_toolkit.monitoring.run_tracker import RunTracker
from backend_toolkit.logger import get_logger
from src.fetch import fetch_source_rows
from src.transform import transform_rows
from src.insert import insert_rows, get_last_inserted_tms_id
from src.config import USER_GUID

logger = get_logger(__name__)

def run_etl():
    with RunTracker("device-log-etl") as run:
        current_run_id = run.run_id 
        
        try:
            last_id = get_last_inserted_tms_id(current_run_id)
            logger.info(
                "log-etl started",
                extra={"last_tms_log_id": last_id, "run_id": current_run_id},
            )

            batch_no = 0
            total_inserted = 0

            while True:
                df = fetch_source_rows(last_id, current_run_id)
                if df.empty:
                    break

                batch_no += 1
                max_id = int(df["id"].max())

                logger.info(
                    "processing batch",
                    extra={
                        "batch_no": batch_no,
                        "from_tms_log_id": last_id + 1,
                        "to_tms_log_id": max_id,
                        "row_count": len(df),
                        "run_id": current_run_id,
                    },
                )

                transformed = transform_rows(df, USER_GUID)
                inserted = insert_rows(transformed, current_run_id)

                total_inserted += inserted
                last_id = max_id

            logger.info(
                "log-etl finished",
                extra={
                    "final_last_tms_log_id": last_id,
                    "batches": batch_no,
                    "rows_inserted": total_inserted,
                    "run_id": current_run_id
                },
            )
            
        except Exception as exc:
            logger.error(
                "log-etl crashed",
                extra={"error": str(exc), "run_id": current_run_id},
                exc_info=True,
            )
            raise
      

if __name__ == "__main__":
    run_etl()
