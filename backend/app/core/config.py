"""Local settings shared by the ASGI server and migrations."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DBMS_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )

    app_db: Path = Path("data/app.sqlite")
    demo_db: Path = Path("data/demo.sqlite")
    demo_enabled: bool = False
    secure_cookies: bool = False
    allowed_origins: frozenset[str] = frozenset({
        "http://127.0.0.1:5173", "http://localhost:5173",
        "http://127.0.0.1:8000", "http://localhost:8000",
    })

    @model_validator(mode="after")
    def separate_database_paths(self) -> "Settings":
        self.app_db = (PROJECT_ROOT / self.app_db).resolve()
        self.demo_db = (PROJECT_ROOT / self.demo_db).resolve()
        same_inode = (
            self.app_db.exists() and self.demo_db.exists() and self.app_db.samefile(self.demo_db)
        )
        if self.app_db == self.demo_db or same_inode:
            raise ValueError("application and demo databases must be separate files")
        return self
