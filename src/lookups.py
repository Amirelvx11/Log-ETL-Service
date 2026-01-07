import re
import uuid
from sqlalchemy import text
from src.config import mssql_engine, USER_GUID
from backend_toolkit.logger import get_logger

logger = get_logger("lookups")

_OS_CACHE: dict[str, str] = {}
_MANAGER_CACHE: dict[str, str] = {}

# ---------------- OS ---------------- #

def normalize_os(value: str) -> tuple[str, str]:
    v = value.strip().upper()

    # SP_BV1.1|42AE → store SP_BV1.1|42AE (EXACTLY)
    if "|" in v:
        return v, v

    # SP_CV6.6A → store as SP_CV6.6
    if v.endswith("A"):
        return v[:-1], v[:-1]

    # SP_CV2.8Y → store SP_CV2.8Y (EXACTLY)
    # SP_CV2.7B → store SP_CV2.7B (EXACTLY)
    return v, v


def ensure_os_exists(raw: str) -> str | None:
    if not raw:
        return None
    
    lookup, insert_val = normalize_os(raw)
    key = lookup

    if key in _OS_CACHE:
        return _OS_CACHE[key]

    try:
        with mssql_engine.begin() as conn:
            row = conn.execute(
                text("""
                    SELECT Id
                    FROM Hamon.mfu.OperatingSystem WITH (NOLOCK)
                    WHERE UPPER(Title) = :t
                """),
                {"t": lookup},
            ).fetchone()

            if row:
                _OS_CACHE[key] = row[0]
                return row[0]

            logger.debug("creating operating system", extra={"title": insert_val})
            
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
    return value if value.startswith(("VS", "VC")) else None


def ensure_manager_exists_exact(raw: str) -> str | None:
    normalized = normalize_manager(raw)
    if not normalized:
        return None
    
    key = normalized.upper()

    if key in _MANAGER_CACHE:
        return _MANAGER_CACHE[key]

    numeric = re.sub(r"^[A-Z]+", "", normalized)

    try:
        with mssql_engine.begin() as conn:
            row = conn.execute(
                text("""
                    SELECT Id FROM Hamon.mfu.Manager WITH (NOLOCK)
                    WHERE
                        UPPER(Title) = :raw
                        OR UPPER(Title) = :numeric
                        OR UPPER(Title) = 'VS' + :numeric
                        OR UPPER(Title) = 'VC' + :numeric
                """),
                {"raw": normalized, "numeric": numeric},
            ).fetchone()

            if row:
                _MANAGER_CACHE[key] = row[0]
                return row[0]

            logger.debug("creating manager version", extra={"title": normalized})

            new_id = str(uuid.uuid4()).upper()
            conn.execute(
                text("""
                    INSERT INTO Hamon.mfu.Manager
                    (Id, Title, IsActive, CreatedBy, CreatedOn,
                    ModifiedBy, ModifiedOn, OwnerId)
                    VALUES
                    (:id, :title, 1, :u, GETDATE(), :u, GETDATE(), :u)
                """),
                {"id": new_id, "title": normalized, "u": USER_GUID},
            )

            _MANAGER_CACHE[key] = new_id
            return new_id

    except Exception as exc:
        logger.error(
            "manager lookup failed",
            extra={
                "raw": raw,
                "normalized": normalized,
                "error": str(exc),
            },
            exc_info=True,
        )
        raise
    