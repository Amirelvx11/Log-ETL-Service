import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
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
                chunksize=1000,
            )

        print(f"Inserted {len(df)} rows into DeviceLog")
        return len(df)

    except SQLAlchemyError as e:
        print(f"Insert failed (rows={len(df)})")
        raise


def get_last_inserted_tms_id() -> int:
    with mssql_engine.begin() as conn:
        row = conn.execute(
            text("SELECT ISNULL(MAX(TmsLogId), 0) FROM Hamon.mfu.DeviceLog")
        ).fetchone()
        return int(row[0])
