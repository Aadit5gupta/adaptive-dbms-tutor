"""SQLite application database connections."""

from pathlib import Path

from sqlalchemy import URL, create_engine, event
from sqlalchemy.engine import Engine


def open_engine(path: Path, *, create: bool = False) -> Engine:
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
        url = URL.create("sqlite+pysqlite", database=str(path))
    else:
        # Opening the web app must not silently create an unmigrated database.
        url = URL.create(
            "sqlite+pysqlite", database=path.as_uri(), query={"uri": "true", "mode": "rw"}
        )
    engine = create_engine(url, connect_args={"timeout": 3}, hide_parameters=True)

    @event.listens_for(engine, "connect")
    def enforce_foreign_keys(connection: object, _: object) -> None:
        # SQLAlchemy supplies the SQLite DB-API connection here.
        from sqlite3 import Connection

        if not isinstance(connection, Connection):
            raise TypeError("expected an SQLite connection")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA recursive_triggers=ON")

    return engine
