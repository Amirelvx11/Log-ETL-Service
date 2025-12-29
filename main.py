import time
from src.config import USER_GUID
from src.fetch import fetch_source_rows
from src.transform import transform_rows
from src.insert import insert_rows, get_last_inserted_tms_id


def run_etl():
    last_id = get_last_inserted_tms_id()
    total_inserted = 0

    print(f"[etl] starting from TmsLogId > {last_id}")

    while True:
        df = fetch_source_rows(last_id)
        if df.empty:
            print("[etl] no more rows")
            break

        rows = transform_rows(df, USER_GUID)
        inserted = insert_rows(rows)

        total_inserted += inserted
        last_id = int(df["id"].max())

        print(f"[etl] fetched={len(df)} inserted={inserted} last_id={last_id}")
        time.sleep(0.1)

    print(f"[etl] finished, total inserted={total_inserted}")


if __name__ == "__main__":
    run_etl()
