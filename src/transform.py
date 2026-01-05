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
    return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")


def _resolve_part_id(terminal: str | None) -> str | None:
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

    for r in df.itertuples(index=False):
            os_id = ensure_os_exists(r.cos_device_version)

            mgr_raw = r.vs_device_version
            if not mgr_raw:
                mgr_raw = r.vc_device_version
            mgr_id = ensure_manager_exists_exact(mgr_raw)

            conn_type = COMM_MODE_MAP.get(r.commode)
            if conn_type is None and r.commode is not None:
                logger.debug(
                    "unknown commode value",
                    extra={"value": r.commode}
                )

            request_type = REQUEST_TYPE_MAP.get(r.request_subject)
            if request_type is None and r.request_subject is not None:
                logger.debug(
                    "unknown request_subject value",
                    extra={"value": r.request_subject}
                )
            
            created_on = _parse_datetime(r.start_time)
                                       
            row = {
                    "Id": str(uuid.uuid4()).upper(),
                    "IsActive": 1,
                    "CreatedBy": user_guid,
                    "CreatedOn": created_on,
                    "ModifiedBy": user_guid,
                    "ModifiedOn": created_on,
                    "OwnerId": user_guid,
                    "TmsLogId": int(r.id),
                    "Tusn": r.serial,
                    "Terminal": r.terminal,
                    "TerminalNumber": r.terminal_number,
                    "BatteryVoltage": r.electricity,
                    "ConnectionType": conn_type,
                    "BaseStation": r.base_station,
                    "ManagerVersionId": mgr_id,
                    "OsVersionId": os_id,
                    "RequestType": request_type,
                    "PartId": _resolve_part_id(r.terminal),
                }
            rows.append(_clean_nan(row))

    df = pd.DataFrame(rows)
    df = df.convert_dtypes()
    return df
