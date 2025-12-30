from datetime import datetime
from typing import List, Dict, Any
import uuid
import math
import pandas as pd
from collections import Counter
from src.config import COMM_MODE_MAP, REQUEST_TYPE_MAP, PART_ID_BY_PREFIX
from src.lookups import ensure_os_exists, ensure_manager_exists_exact

error_stats = Counter()

#-----------------------HELPER METHODS-----------------------#

def parse_datetime(value) -> datetime:
    if value is None or pd.isna(value):
        raise ValueError("start_time is NULL/NaN")

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError(f"Invalid start_time string: {value}")

    raise ValueError(f"Unsupported start_time type: {type(value)}")


def clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in row.items():
        if isinstance(v, float) and math.isnan(v):
            row[k] = None
    return row


def resolve_part_id(terminal: str) -> str | None:
    if not terminal:
        return None
    for prefix, guid in PART_ID_BY_PREFIX.items():
        if terminal.startswith(prefix):
            return guid
    return None

#-----------------------CORE TRANSFORM-----------------------#

def transform_rows(df: pd.DataFrame, user_guid: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    errors = 0

    for _, r in df.iterrows(): #for batch<10k is ok (default batch size:2000)
        try:
            os_id = ensure_os_exists(r.get("cos_device_version"))

            mgr_raw = r.get("vc_device_version")
            if not mgr_raw:
                mgr_raw = r.get("vs_device_version")
                
            mgr_id = ensure_manager_exists_exact(mgr_raw)
            created_on = parse_datetime(r.get("start_time"))
            part_id = resolve_part_id(r.get("terminal"))


            row = {
                    "Id": str(uuid.uuid4()).upper(),
                    "IsActive": 1,
                    "CreatedBy": user_guid,
                    "CreatedOn": created_on,
                    "ModifiedBy": user_guid,
                    "ModifiedOn": created_on,
                    "OwnerId": user_guid,
                    "TmsLogId": int(r["id"]),
                    "Tusn": r.get("serial"),
                    "Terminal": r.get("terminal"),
                    "TerminalNumber": r.get("terminal_number"),
                    "BatteryVoltage": r.get("electricity"),
                    "ConnectionType": COMM_MODE_MAP.get(r.get("commode")),
                    "BaseStation": r.get("base_station"),
                    "ManagerVersionId": mgr_id,
                    "OsVersionId": os_id,
                    "RequestType": REQUEST_TYPE_MAP.get(r.get("request_subject")),
                    "PartId": part_id,
                }
            rows.append(clean_row(row))

        except Exception as e:
            errors += 1
            error_stats[type(e).__name__] += 1

            print(
                f"[transform][skip] id={r.get('id')} "
                f"error={type(e).__name__} msg={e}"
            )

    if error_stats:
        print(f"[transform][errors] {dict(error_stats)}")

    return pd.DataFrame(rows)
