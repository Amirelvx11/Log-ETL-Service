from typing import List, Dict, Any
from sqlalchemy import text
from src.config import mssql_engine


INSERT_SQL = text("""
INSERT INTO Hamon.mfu.DeviceLog
(
    Id, IsActive, CreatedBy, CreatedOn, ModifiedBy, ModifiedOn, OwnerId,
    TmsLogId, Tusn, Terminal, TerminalNumber, BatteryVoltage,
    ConnectionType, BaseStation, ManagerVersionId, OsVersionId,
    RequestType, PartId
)
VALUES
(
    :Id, :IsActive, :CreatedBy, :CreatedOn, :ModifiedBy, :ModifiedOn, :OwnerId,
    :TmsLogId, :Tusn, :Terminal, :TerminalNumber, :BatteryVoltage,
    :ConnectionType, :BaseStation, :ManagerVersionId, :OsVersionId,
    :RequestType, :PartId
)
""")


def insert_rows(rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0

    with mssql_engine.begin() as conn:
        raw = conn.connection
        cursor = raw.cursor()
        cursor.fast_executemany = True

        cursor.executemany(
            INSERT_SQL.text,
            rows
        )

        return cursor.rowcount


def get_last_inserted_tms_id() -> int:
    with mssql_engine.begin() as conn:
        row = conn.execute(
            text("SELECT ISNULL(MAX(TmsLogId), 0) FROM Hamon.mfu.DeviceLog")
        ).fetchone()
        return int(row[0])
