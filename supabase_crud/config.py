"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _get_val(name: str, default: str = "") -> str:
    val = os.getenv(name, "").strip()
    if not val:
        try:
            import streamlit as st

            if name in st.secrets:
                val = str(st.secrets[name]).strip()
        except Exception:
            pass
    return val or default


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

        url = _get_val("SUPABASE_URL")
        key = (
            _get_val("SUPABASE_SERVICE_ROLE_KEY")
            or _get_val("SUPABASE_SECRET_KEY")
            or _get_val("SUPABASE_KEY")
        )
        if not url:
            raise ConfigurationError("SUPABASE_URL is required. Copy it into .env or Streamlit Secrets.")
        if not key:
            raise ConfigurationError(
                "SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) is required."
            )

        raw_limit = _get_val("MAX_FILE_SIZE_BYTES", str(10 * 1024 * 1024))
        try:
            max_file_size = int(raw_limit)
        except ValueError as exc:
            raise ConfigurationError("MAX_FILE_SIZE_BYTES must be an integer.") from exc
        if max_file_size <= 0:
            raise ConfigurationError("MAX_FILE_SIZE_BYTES must be greater than zero.")

        return cls(
            supabase_url=url.rstrip("/"),
            supabase_key=key,
            bucket=_get_val("SUPABASE_BUCKET", "documents") or "documents",
            edge_function_name=_get_val("EDGE_FUNCTION_NAME", "validate-upload") or "validate-upload",
            edge_function_secret=_get_val("EDGE_FUNCTION_SECRET"),
            app_user=_get_val("APP_USER", "terminal-user") or "terminal-user",
            max_file_size_bytes=max_file_size,
        )

