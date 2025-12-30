import pandas as pd
from sqlalchemy import text
from src.config import mssql_engine


def insert_rows(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    with mssql_engine.begin() as conn:
        df.to_sql(
            name="DeviceLog",
            schema="mfu",
            con=conn,
            if_exists="append",
            index=False,
            chunksize=1000,
        )

    return len(df)


def get_last_inserted_tms_id() -> int:
    with mssql_engine.connect() as conn:
        return int(
            conn.execute(
                text("SELECT ISNULL(MAX(TmsLogId),0) FROM Hamon.mfu.DeviceLog")
            ).scalar_one()
        )
