import re
import uuid
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.config import mssql_engine, USER_GUID


# ---------- NORMALIZATION ----------
def normalize_os(value: str) -> str:
    if not value:
        return ""
    value = value.strip().upper()
    return re.sub(r"[A-Z]$", "", value)


def manager_exact(value: str) -> str:
    return value.strip().upper() if value else ""


def manager_short(value: str) -> str:
    v = manager_exact(value)
    return v[2:] if len(v) > 2 and v[:2].isalpha() else v


# ---------- ENSURE OS ----------
def ensure_os_exists(raw: str) -> str | None:
    title = normalize_os(raw)
    if not title:
        return None

    sql_sel = "SELECT Id FROM Hamon.mfu.OperatingSystem WHERE UPPER(Title) = :t"

    with mssql_engine.begin() as conn:
        row = conn.execute(text(sql_sel), {"t": title}).fetchone()
        if row:
            return row[0]

        new_id = str(uuid.uuid4()).upper()
        sql_ins = """
        INSERT INTO Hamon.mfu.OperatingSystem
        (Id, Title, IsActive, CreatedBy, CreatedOn, ModifiedBy, ModifiedOn, OwnerId, Description)
        VALUES (:id, :title, 1, :u, GETDATE(), :u, GETDATE(), :u, NULL)
        """
        conn.execute(
            text(sql_ins),
            {
                "id": new_id,
                "title": title,
                "u": USER_GUID,
            },
        )
        print(f"[OS] Inserted new OS: {title}")
        return new_id


# ---------- ENSURE MANAGER ----------
def ensure_manager_exists(raw: str) -> str | None:
    exact = manager_exact(raw)
    if not exact:
        return None

    short = manager_short(raw)
    sql_sel = "SELECT Id FROM Hamon.mfu.Manager WHERE UPPER(Title) = :t"

    with mssql_engine.begin() as conn:
        r1 = conn.execute(text(sql_sel), {"t": exact}).fetchone()
        if r1:
            return r1[0]

        r2 = conn.execute(text(sql_sel), {"t": short}).fetchone()
        if r2:
            return r2[0]

        new_id = str(uuid.uuid4()).upper()
        sql_ins = """
        INSERT INTO Hamon.mfu.Manager
        (Id, Title, IsActive, CreatedBy, CreatedOn, ModifiedBy, ModifiedOn, OwnerId, Description)
        VALUES (:id, :title, 1, :u, GETDATE(), :u, GETDATE(), :u, NULL)
        """
        conn.execute(
            text(sql_ins),
            {
                "id": new_id,
                "title": exact,
                "u": USER_GUID,
            },
        )
        print(f"[Manager] Inserted new Manager: {exact}")
        return new_id


# ---------- PRELOAD MAP ----------
def fetch_lookup_maps():
    try:
        with mssql_engine.connect() as conn:
            os_df = pd.read_sql(
                "SELECT Id, Title FROM Hamon.mfu.OperatingSystem WITH (NOLOCK)",
                conn,
            )
            mgr_df = pd.read_sql(
                "SELECT Id, Title FROM Hamon.mfu.Manager WITH (NOLOCK)",
                conn,
            )

        os_map = {
            normalize_os(r["Title"]): r["Id"]
            for _, r in os_df.iterrows()
        }
        mgr_exact = {
            manager_exact(r["Title"]): r["Id"]
            for _, r in mgr_df.iterrows()
        }
        mgr_short = {
            manager_short(r["Title"]): r["Id"]
            for _, r in mgr_df.iterrows()
        }

        return os_map, mgr_exact, mgr_short

    except SQLAlchemyError as e:
        print(f"[fetch_lookup_maps] error: {e}")
        return {}, {}, {}
