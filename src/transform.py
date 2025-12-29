from datetime import datetime
from typing import List, Dict, Any
import uuid
import pandas as pd

from src.constants import (
    COMM_MODE_MAP,
    REQUEST_TYPE_MAP,
    PART_ID_BY_PREFIX,
)

# ------------------------
# Utilities
# ------------------------

def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        # Example: "2024-01-13 15:42:11"
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


# ------------------------
# Core Transform
# ------------------------

def transform_rows(
    df: pd.DataFrame,
    os_map: dict,
    mgr_map_exact: dict,
    mgr_map_short: dict,
    ensure_os_fn,
    ensure_mgr_fn,
    user_guid: str,
) -> List[Dict[str, Any]]:
    """
    Pure transformation:
    - No DB writes here (except via injected ensure_* functions)
    - Returns list of dicts ready for INSERT
    """

    rows: List[Dict[str, Any]] = []
    errors = 0

    for _, r in df.iterrows():
        try:
            os_raw = r.get("cos_device_version")
            mgr_src = r.get("vc_device_version") or r.get("vs_device_version")

            os_key = os_raw.strip().upper() if os_raw else ""
            mgr_key = mgr_src.strip().upper() if mgr_src else ""

            os_id = os_map.get(os_key)
            if not os_id and os_key:
                os_id = ensure_os_fn(os_key)
                if os_id:
                    os_map[os_key] = os_id

            mgr_id = mgr_map_exact.get(mgr_key) or mgr_map_short.get(mgr_key)
            if not mgr_id and mgr_key:
                mgr_id = ensure_mgr_fn(mgr_key)
                if mgr_id:
                    mgr_map_exact[mgr_key] = mgr_id

            created_on = parse_datetime(r.get("start_time"))
            part_id = resolve_part_id(r.get("terminal"))

            if not part_id:
                raise ValueError("Unknown terminal prefix")

            record = {
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

            rows.append(record)

        except Exception as e:
            errors += 1
            print(f"[transform] skip id={r.get('id')}: {e}")
            
    if errors:
        print(f"[transform] skipped {errors} rows")

    return rows
