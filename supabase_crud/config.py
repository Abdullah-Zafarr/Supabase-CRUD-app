"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    bucket: str = "documents"
    edge_function_name: str = "validate-upload"
    edge_function_secret: str = ""
    app_user: str = "terminal-user"
    max_file_size_bytes: int = 10 * 1024 * 1024

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        url = os.getenv("SUPABASE_URL", "").strip()
        # SUPABASE_KEY is supported as a convenient generic alias, while the
        # documented name makes it clear that this is a server-side key.
        key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
            or os.getenv("SUPABASE_SECRET_KEY", "").strip()
            or os.getenv("SUPABASE_KEY", "").strip()
        )
        if not url:
            raise ConfigurationError("SUPABASE_URL is required. Copy it into .env.")
        if not key:
            raise ConfigurationError(
                "SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) is required."
            )

        raw_limit = os.getenv("MAX_FILE_SIZE_BYTES", str(10 * 1024 * 1024))
        try:
            max_file_size = int(raw_limit)
        except ValueError as exc:
            raise ConfigurationError("MAX_FILE_SIZE_BYTES must be an integer.") from exc
        if max_file_size <= 0:
            raise ConfigurationError("MAX_FILE_SIZE_BYTES must be greater than zero.")

        return cls(
            supabase_url=url.rstrip("/"),
            supabase_key=key,
            bucket=os.getenv("SUPABASE_BUCKET", "documents").strip() or "documents",
            edge_function_name=(
                os.getenv("EDGE_FUNCTION_NAME", "validate-upload").strip()
                or "validate-upload"
            ),
            edge_function_secret=os.getenv("EDGE_FUNCTION_SECRET", "").strip(),
            app_user=os.getenv("APP_USER", "terminal-user").strip() or "terminal-user",
            max_file_size_bytes=max_file_size,
        )

