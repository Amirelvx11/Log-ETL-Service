import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
from pymongo import MongoClient


IRAN = ZoneInfo("Asia/Tehran")

ALLOWED_START = dt_time(22, 0)
ALLOWED_END = dt_time(8, 0)

# scheduler: runs every 30 min, ticks every 60s
HEALTH_WINDOW_MINUTES = 120  # interval × 4 (safe)


def within_allowed_window(now: datetime) -> bool:
    """22:00 → 08:00 overnight window"""
    t = now.time()
    return t >= ALLOWED_START or t <= ALLOWED_END


def main() -> None:
    REQUIRED = [
        "BT_MONGO_URI",
        "BT_MONGO_DB",
        "BT_MONGO_COLLECTION",
        "BT_APP_NAME",
        "BT_ENVIRONMENT",
        "SOURCE_DB",
        "TARGET_DB",
        "USER_GUID",
    ]

    for key in REQUIRED:
        if not os.getenv(key):
            sys.exit(1)

    now = datetime.now(IRAN)
    cutoff = now - timedelta(minutes=HEALTH_WINDOW_MINUTES)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    # --- Mongo ---
    client = MongoClient(
        os.environ["BT_MONGO_URI"],
        serverSelectionTimeoutMS=3000,
    )
    client.admin.command("ping")

    col = client[
        os.environ["BT_MONGO_DB"]
    ][
        os.environ["BT_MONGO_COLLECTION"]
    ]

    base_query = {
        "app": os.environ["BT_APP_NAME"],
        "environment": os.environ["BT_ENVIRONMENT"],
        "timestamp": {"$gte": cutoff_str},
    }

    # --- Recent activity (scheduler / ETL ran or ticked) ---
    last_log = col.find_one(
        base_query,
        sort=[("timestamp", -1)],
    )

    if within_allowed_window(now):
        if not last_log:
            sys.exit(1)
    else:
        if not last_log:
            pass

    # --- Error detection ---
    error_log = col.find_one(
        {
            **base_query,
            "level": {"$in": ["ERROR", "CRITICAL"]},
        }
    )
    if error_log:
        sys.exit(1)

    # --- Scheduler / ETL marker validation ---
    if last_log:
        msg = (last_log.get("message") or "").lower()

        HEALTHY_MARKERS = (
            "scheduler",
            "log-etl",
            "starting",
	        "started",
            "finished",
            "running",
            "inserted",
            "executed",
            "processing",
        )

        if not any(m in msg for m in HEALTHY_MARKERS):
            sys.exit(1)

    # --- DB Connection Check ---
    try:
        engine1 = create_engine(
            os.environ["SOURCE_DB"],
            pool_pre_ping=True,
            pool_timeout=3,
        )
        with engine1.connect() as conn:
            conn.execute(text("SELECT 1"))

        engine2 = create_engine(
            os.environ["TARGET_DB"],
            pool_pre_ping=True,
            pool_timeout=3,
        )
        with engine2.connect() as conn:
            conn.execute(text("SELECT 1"))

    except SQLAlchemyError as e:
        raise RuntimeError(f"DB check failed: {e}") from e

    sys.exit(0)


if __name__ == "__main__":
    main()
