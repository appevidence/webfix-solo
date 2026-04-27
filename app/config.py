# Ported from appevidence/evidence-capture-app at commit c59d756a4cdb2f40d0b9a3570f411880d2df1c4c
from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WEBFIX_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    data_dir: Path = Path("~/.local/share/webfix-solo")
    db_path: Path | None = None
    signing_key_path: Path | None = None
    bundles_dir: Path | None = None
    audit_log_path: Path | None = None
    capture_timeout: int = 60
    capture_headless: bool = True
    capture_viewport_width: int = 1280
    capture_viewport_height: int = 800
    tsa_url: str = "http://timestamp.digicert.com"
    log_level: str = "INFO"
    max_retries: int = 3

    @field_validator("data_dir", mode="before")
    @classmethod
    def _expand_data_dir(cls, v: str | Path) -> Path:
        return Path(v).expanduser()

    @property
    def resolved_db_path(self) -> Path:
        return self.db_path or (self.data_dir / "db.sqlite")

    @property
    def resolved_signing_key_path(self) -> Path:
        return self.signing_key_path or (self.data_dir / "keys/signing.key")

    @property
    def resolved_bundles_dir(self) -> Path:
        return self.bundles_dir or (self.data_dir / "bundles")

    @property
    def resolved_audit_log_path(self) -> Path:
        return self.audit_log_path or (self.data_dir / "audit.log")


settings = Settings()
