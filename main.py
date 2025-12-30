import time
from src.config import USER_GUID
from src.fetch import fetch_source_rows
from src.transform import transform_rows
from src.insert import insert_rows, get_last_inserted_tms_id


def run_etl():
    start_ts = time.time()
    batch_start = time.time()

    last_id = get_last_inserted_tms_id()
    total_inserted = 0
    batches = 0

    print(f"[etl] start last_tms_id={last_id}")

    while True:
        df = fetch_source_rows(last_id)
        if df.empty:
            print("[etl] no more rows to fetch")
            break

        batches += 1

        df_transformed = transform_rows(df, USER_GUID)
        inserted = insert_rows(df_transformed)

        total_inserted += inserted
        last_id = int(df["id"].max())
        
        batch_time = round(time.time() - batch_start, 2)

        print(
            f"[etl][batch={batches}] "
            f"fetched={len(df)} transformed={len(df_transformed)} "
            f"inserted={inserted} "
            f"last_id={last_id} "
            f"time_sec={batch_time}"
        )

        time.sleep(0.1)

    duration = round(time.time() - start_ts, 2)
    print(
        f"[etl] finished batches={batches} "
        f"total_inserted={total_inserted} "
        f"duration_sec={duration}"
    )



if __name__ == "__main__":
    run_etl()
