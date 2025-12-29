from datetime import datetime
from typing import List, Dict, Any
import uuid
import pandas as pd
from src.config import COMM_MODE_MAP, REQUEST_TYPE_MAP, PART_ID_BY_PREFIX
from src.lookups import ensure_os_exists, ensure_manager_exists_exact


# ---------------- Utilities ---------------- #

def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def resolve_part_id(terminal: str) -> str | None:
    if not terminal:
        return None
    for prefix, guid in PART_ID_BY_PREFIX.items():
        if terminal.startswith(prefix):
            return guid
    return None


# ---------------- Core Transform ---------------- #

def transform_rows(df: pd.DataFrame, user_guid: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    errors = 0

    for _, r in df.iterrows():
        try:
            os_id = ensure_os_exists(r.get("cos_device_version"))

            mgr_raw = r.get("vc_device_version") or r.get("vs_device_version")
            mgr_id = ensure_manager_exists_exact(mgr_raw)
            
            if not created_on:
                raise ValueError("Invalid start_time")            
            created_on = parse_datetime(r.get("start_time"))
            
            part_id = resolve_part_id(r.get("terminal"))
            if not part_id:
                raise ValueError("Unknown terminal prefix")

            rows.append(
                {
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
            )

        except Exception as e:
            errors += 1
            print(f"[transform] skip id={r.get('id')}: {e}")

    if errors:
        print(f"[transform] skipped {errors} rows")

    return rows
