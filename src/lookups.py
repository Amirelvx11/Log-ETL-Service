import re
import uuid
from sqlalchemy import text
from src.config import mssql_engine, USER_GUID
from backend_toolkit.logger import get_logger

logger = get_logger(__name__)


_OS_CACHE: dict[str, str] = {}
_MANAGER_CACHE: dict[str, str] = {}


# ---------------- OS ---------------- #

def normalize_os(value: str) -> tuple[str, str]:
    v = value.strip().upper()

    if "|" in v:
        return v, v

    m = re.match(r"^(.*?)([A-Z])$", v)
    if not m:
        return v, v

    base, suffix = m.groups()
    return (base, base) if suffix == "A" else (v, v)


def ensure_os_exists(raw: str) -> str | None:
    if not raw:
        return None
    
    try:
        lookup, insert_val = normalize_os(raw)
        key = lookup.upper()

        if key in _OS_CACHE:
            return _OS_CACHE[key]

        with mssql_engine.begin() as conn:
            row = conn.execute(
                text("SELECT Id FROM Hamon.mfu.OperatingSystem WHERE UPPER(Title) = :t"),
                {"t": lookup},
            ).fetchone()

            if row:
                _OS_CACHE[key] = row[0]
                return row[0]

            logger.info("creating operating system", extra={"title": insert_val})
            
            new_id = str(uuid.uuid4()).upper()
            conn.execute(
                text("""
                    INSERT INTO Hamon.mfu.OperatingSystem
                    (Id, Title, IsActive, CreatedBy,
                    CreatedOn, ModifiedBy, ModifiedOn, OwnerId)
                    VALUES
                    (:id, :title, 1, :u, GETDATE(), :u, GETDATE(), :u)
                """),
                {"id": new_id, "title": insert_val, "u": USER_GUID},
            )

            _OS_CACHE[key] = new_id
            return new_id
        
    except Exception as exc:
        logger.error(
            "os lookup failed",
            extra={"raw": raw, "error": str(exc)},
        )
        raise

# ---------------- MANAGER ---------------- #

def normalize_manager(value: str) -> str | None:
    if not value:
        return None

    value = value.strip().upper()
    return value if value.startswith("V") else None


def ensure_manager_exists_exact(raw: str) -> str | None:
    normalized = normalize_manager(raw)
    if not normalized:
        return None
    
    try:
        key = normalized.upper()

        if key in _MANAGER_CACHE:
            return _MANAGER_CACHE[key]

        numeric = re.sub(r"^[A-Z]+", "", normalized)

        logger.info("creating manager version", extra={"title": raw})

        with mssql_engine.begin() as conn:
            row = conn.execute(
                text("""
                    SELECT Id FROM Hamon.mfu.Manager
                    WHERE
                        UPPER(Title) = :raw
                        OR UPPER(Title) = :numeric
                        OR UPPER(Title) = 'VS' + :numeric
                        OR UPPER(Title) = 'VC' + :numeric
                """),
                {"raw": raw, "numeric": numeric},
            ).fetchone()

            if row:
                _MANAGER_CACHE[key] = row[0]
                return row[0]

            new_id = str(uuid.uuid4()).upper()
            conn.execute(
                text("""
                    INSERT INTO Hamon.mfu.Manager
                    (Id, Title, IsActive, CreatedBy, CreatedOn,
                    ModifiedBy, ModifiedOn, OwnerId)
                    VALUES
                    (:id, :title, 1, :u, GETDATE(), :u, GETDATE(), :u)
                """),
                {"id": new_id, "title": raw, "u": USER_GUID},
            )

            _MANAGER_CACHE[key] = new_id
            return new_id

    except Exception as exc:
        logger.error(
            "manager lookup failed",
            extra={"raw": raw, "error": str(exc)},
        )
        raise