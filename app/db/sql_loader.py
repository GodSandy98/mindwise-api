from pathlib import Path
from functools import lru_cache
from sqlalchemy import text, bindparam
from sqlalchemy.sql.elements import TextClause


@lru_cache(maxsize=64)
def load_sql(name: str) -> str:
    """
    Load SQL from app/sql/<name>.sql with caching.
    """
    base_dir = Path(__file__).resolve().parents[1]  # app/
    sql_path = base_dir / "sql" / f"{name}.sql"
    return sql_path.read_text(encoding="utf-8")


def load_text_query(name: str, expanding_params: tuple[str, ...] = ()) -> TextClause:
    """
    Return sqlalchemy.text() for a named SQL file, optionally enabling expanding IN params.
    """
    stmt = text(load_sql(name))
    for p in expanding_params:
        stmt = stmt.bindparams(bindparam(p, expanding=True))
    return stmt
