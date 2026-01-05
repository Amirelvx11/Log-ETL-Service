import os
import time
import socket
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
from backend_toolkit.logger import get_logger
from main import run_etl

logger = get_logger("log-etl-scheduler")

IRAN = ZoneInfo("Asia/Tehran")

CHECK_INTERVAL_SECONDS = 1800  # 30 minutes
SLEEP_TICK_SECONDS = 60        # fine‑grained scheduler tick

ALLOWED_START = dt_time(22, 0)
ALLOWED_END   = dt_time(8, 0)

last_run_started_at: datetime | None = None
is_running = False


def validate_env() -> None:
    required_vars = [
        "SOURCE_DB",
        "TARGET_DB",
        "USER_GUID",
    ]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.critical(
            "Missing required environment variables",
            extra={"missing_vars": missing},
        )
        raise RuntimeError(f"Missing env vars: {missing}")


def within_allowed_window(now: datetime) -> bool:
    """Handles overnight window (22:00 → 08:00)."""
    t = now.time()
    return t >= ALLOWED_START or t <= ALLOWED_END


def allowed_by_interval(now: datetime) -> bool:
    if last_run_started_at is None:
        return True

    return (now - last_run_started_at) >= timedelta(
        seconds=CHECK_INTERVAL_SECONDS
    )

def main() -> None:
    global last_run_started_at, is_running

    validate_env()

    logger.info(
        "Log-ETL scheduler started",
        extra={
            "timezone": "Asia/Tehran",
            "window": "22:00-08:00",
            "interval_seconds": CHECK_INTERVAL_SECONDS,
            "hostname": socket.gethostname(),
        },
    )

    while True:
        now = datetime.now(IRAN)

        try:
            if is_running:
                logger.warning("ETL still running, skipping tick")
                time.sleep(SLEEP_TICK_SECONDS)
                continue
            
            if within_allowed_window(now) and allowed_by_interval(now):
                logger.info(
                    "Starting Log-ETL run",
                    extra={"previous_run": last_run_started_at},
                )

                is_running = True
                started_at = datetime.now(IRAN)

                run_etl()

                last_run_started_at = started_at
                is_running = False

            else:
                logger.debug(
                    "Not eligible for run",
                    extra={
                        "within_window": within_allowed_window(now),
                        "last_run": last_run_started_at,
                    },
                )

        except Exception:
            is_running = False
            logger.error("Scheduler execution error", exc_info=True)

        time.sleep(SLEEP_TICK_SECONDS)


if __name__ == "__main__":
    main()
