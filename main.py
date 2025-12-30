import time
from src.fetch import fetch_source_rows
from src.transform import transform_rows
from src.insert import insert_rows, get_last_inserted_tms_id
from src.config import USER_GUID


def run_etl():
    last_id = get_last_inserted_tms_id()

    print(f"[etl] start last_tms_id={last_id}")

    while True:
        df = fetch_source_rows(last_id)
        if df.empty:
            break

        transformed = transform_rows(df, USER_GUID)
        insert_rows(transformed)
        
        last_id = int(df["id"].max())
        time.sleep(0.05)
        

if __name__ == "__main__":
    run_etl()
