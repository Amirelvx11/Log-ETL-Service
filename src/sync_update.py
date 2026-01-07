from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from backend_toolkit.logger import get_logger
from src.config import mssql_engine, USER_GUID

logger = get_logger("sync_update")

SYNC_SQL = text("""
WITH LatestDeviceLog AS (
    SELECT
        dl.Tusn,
        dl.OsVersionId,
        dl.ManagerVersionId,
        ROW_NUMBER() OVER (
            PARTITION BY dl.Tusn
            ORDER BY dl.TmsLogId DESC
        ) AS rn
    FROM Hamon.mfu.DeviceLog dl WITH (NOLOCK)
    WHERE dl.TmsLogId > :from_id
      AND dl.TmsLogId <= :to_id
      AND dl.Tusn IS NOT NULL
      AND LTRIM(RTRIM(dl.Tusn)) <> ''
      AND dl.OsVersionId IS NOT NULL
      AND dl.ManagerVersionId IS NOT NULL
)
UPDATE p
SET
    p.OsVersionId      = ld.OsVersionId,
    p.ManagerVersionId = ld.ManagerVersionId,
    p.ModifiedOn       = GETDATE(),
    p.ModifiedBy       = :modified_by
FROM Hamon.mfu.Product p WITH (NOLOCK)
JOIN LatestDeviceLog ld
    ON p.Tusn = ld.Tusn
WHERE ld.rn = 1
  AND p.Tusn IS NOT NULL
  AND LTRIM(RTRIM(p.Tusn)) <> ''
  AND (
        p.OsVersionId <> ld.OsVersionId
     OR p.ManagerVersionId <> ld.ManagerVersionId
  );
""")


def sync_update_product_versions(
    *,
    from_id: int,
    to_id: int,
    run_id: str,
) -> int:
    """
    Update Product OS/Manager versions using ONLY logs inserted
    in the current ETL batch.
    """

    if from_id >= to_id:
        return 0

    try:
        with mssql_engine.begin() as conn:
            result = conn.execute(
                SYNC_SQL,
                {
                    "from_id": from_id,
                    "to_id": to_id,
                    "modified_by": str(USER_GUID),
                },
            )

            affected = result.rowcount or 0

        logger.info(
            "product-version-sync executed",
            extra={
                "from_tms_log_id": from_id + 1,
                "to_tms_log_id": to_id,
                "rows_updated": affected,
                "run_id": run_id,
            },
        )

        return affected

    except SQLAlchemyError as exc:
        logger.error(
            "product-version-sync failed",
            extra={
                "from_tms_log_id": from_id + 1,
                "to_tms_log_id": to_id,
                "error": str(exc),
                "run_id": run_id,
            },
            exc_info=True,
        )
        raise
