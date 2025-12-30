import uuid
import math
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from src.config import COMM_MODE_MAP, REQUEST_TYPE_MAP, PART_ID_BY_PREFIX
from src.lookups import ensure_os_exists, ensure_manager_exists_exact
from backend_toolkit.logger import get_logger

logger = get_logger(__name__)


#-----------------------HELPER METHODS-----------------------#

def _parse_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")

    raise ValueError("Invalid start_time")


def _resolve_part_id(terminal: str) -> str | None:
    if not terminal:
        return None

    for prefix, guid in PART_ID_BY_PREFIX.items():
        if terminal.startswith(prefix):
            return guid
    return None


def _clean_nan(row: dict[str, Any]) -> dict[str, Any]:
    for k, v in row.items():
        if isinstance(v, float) and math.isnan(v):
            row[k] = None
    return row

#-----------------------CORE TRANSFORM-----------------------#

def transform_rows(df: pd.DataFrame, user_guid: str) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, r in df.iterrows():
            os_id = ensure_os_exists(r.get("cos_device_version"))

            mgr_raw = r.get("vc_device_version")
            if not mgr_raw:
                mgr_raw = r.get("vs_device_version")
            mgr_id = ensure_manager_exists_exact(mgr_raw)

            conn_type = COMM_MODE_MAP.get(r.get("commode"))
            if conn_type is None and r.get("commode") is not None:
                logger.warning(
                    "unknown commode value",
                    extra={"value": r.get("commode")}
                )

            request_type = REQUEST_TYPE_MAP.get(r.get("request_subject"))
            if request_type is None and r.get("request_subject") is not None:
                logger.warning(
                    "unknown request_subject value",
                    extra={"value": r.get("request_subject")}
                )
                           
            row = {
                    "Id": str(uuid.uuid4()).upper(),
                    "IsActive": 1,
                    "CreatedBy": user_guid,
                    "CreatedOn": _parse_datetime(r.get("start_time")),
                    "ModifiedBy": user_guid,
                    "ModifiedOn": _parse_datetime(r.get("start_time")),
                    "OwnerId": user_guid,
                    "TmsLogId": int(r["id"]),
                    "Tusn": r.get("serial"),
                    "Terminal": r.get("terminal"),
                    "TerminalNumber": r.get("terminal_number"),
                    "BatteryVoltage": r.get("electricity"),
                    "ConnectionType": conn_type,
                    "BaseStation": r.get("base_station"),
                    "ManagerVersionId": mgr_id,
                    "OsVersionId": os_id,
                    "RequestType": request_type,
                    "PartId": _resolve_part_id(r.get("terminal")),
                }
            rows.append(_clean_nan(row))

    return pd.DataFrame(rows)
