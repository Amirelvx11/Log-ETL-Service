import re
import uuid
from sqlalchemy import text
from src.config import mssql_engine, USER_GUID


_OS_CACHE: dict[str, str] = {}
_MANAGER_CACHE: dict[str, int] = {}

# ---------------- OS ---------------- #

def normalize_os_input(value: str) -> tuple[str, str]:
    v = value.strip().upper()

    if "|" in v:
        return v, v

    m = re.match(r"^(.*?)([A-Z])$", v)
    if not m:
        return v, v

    base, suffix = m.groups()

    if suffix == "A":
        return base, base

    return v, v


def ensure_os_exists(raw: str) -> str | None:
    if not raw:
        return None

    lookup, insert_val = normalize_os_input(raw)
    key = lookup.upper()

    cached = _OS_CACHE.get(key)
    if cached is not None:
        return cached

    with mssql_engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT Id
                FROM Hamon.mfu.OperatingSystem
                WHERE UPPER(Title) = :t
            """),
            {"t": lookup},
        ).fetchone()

        if row:
            _OS_CACHE[key] = row[0]
            return row[0]

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


# ---------------- MANAGER ---------------- #

def normalize_manager_input(value: str) -> str | None:
    if not value:
        return None

    value = value.strip().upper()
    if not value.startswith("V"):
        return None

    return value


def extract_manager_numeric(value: str) -> str:
    return re.sub(r"^[A-Z]+", "", value)


def ensure_manager_exists_exact(raw: str) -> str | None:
    normalized = normalize_manager_input(raw)
    if not normalized:
        return None
    numeric = extract_manager_numeric(raw)

    key = normalized.upper()
    cached = _MANAGER_CACHE.get(key)
    if cached is not None:
        return cached

    with mssql_engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT Id
                FROM Hamon.mfu.Manager
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
