"""Business logic for Storage files and their Postgres metadata rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from supabase import Client, create_client

from .config import ConfigurationError, Settings
from .helpers import content_type_for, is_safe_storage_path, storage_path_for


TABLE_NAME = "file_records"


class FileService:
    """Coordinates Storage and Postgres so the CLI exposes simple CRUD calls."""

    def __init__(self, settings: Settings, client: Client | None = None) -> None:
        self.settings = settings
        self.client = client or create_client(settings.supabase_url, settings.supabase_key)

    def _require_edge_secret(self) -> str:
        if not self.settings.edge_function_secret:
            raise ConfigurationError(
                "EDGE_FUNCTION_SECRET is required for upload validation."
            )
        return self.settings.edge_function_secret

    def _get_record(self, record_id: str) -> dict[str, Any]:
        response = (
            self.client.table(TABLE_NAME)
            .select("*")
            .eq("id", record_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise ValueError(f"No file record exists with id {record_id}.")
        return rows[0]

    def _insert_record(self, values: dict[str, Any]) -> dict[str, Any]:
        response = (
            self.client.table(TABLE_NAME)
            .insert(values)
            .select("*")
            .single()
            .execute()
        )
        return response.data

    def _update_record(self, record_id: str, values: dict[str, Any]) -> dict[str, Any]:
        response = (
            self.client.table(TABLE_NAME)
            .update(values)
            .eq("id", record_id)
            .select("*")
            .single()
            .execute()
        )
        return response.data

    def _delete_record(self, record_id: str) -> None:
        self.client.table(TABLE_NAME).delete().eq("id", record_id).execute()

    def _invoke_validator(self, payload: dict[str, Any]) -> Any:
        response = self.client.functions.invoke(
            self.settings.edge_function_name,
            invoke_options={
                "headers": {"x-edge-function-secret": self._require_edge_secret()},
                "body": payload,
            },
        )
        # supabase-py returns a FunctionResponse. Keeping this adapter tolerant
        # of dict-like responses makes the service straightforward to fake in tests.
        if hasattr(response, "data"):
            return response.data
        if isinstance(response, dict):
            return response
        return response

    def _remove_storage_file(self, bucket: str, path: str) -> None:
        if not is_safe_storage_path(path):
            raise ValueError(f"Refusing unsafe Storage path: {path!r}")
        self.client.storage.from_(bucket).remove([path])

    def list_files(self) -> list[dict[str, Any]]:
        response = (
            self.client.table(TABLE_NAME)
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def get_file(self, record_id: str) -> dict[str, Any]:
        return self._get_record(record_id)

    def create_file(self, local_path: str, description: str | None = None) -> dict[str, Any]:
        source = Path(local_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"File does not exist: {source}")
        size = source.stat().st_size
        if size > self.settings.max_file_size_bytes:
            raise ValueError(
                f"File is {size} bytes; the configured limit is "
                f"{self.settings.max_file_size_bytes} bytes."
            )

        storage_path = storage_path_for(source.name)
        content_type = content_type_for(source)
        record = self._insert_record(
            {
                "bucket_name": self.settings.bucket,
                "storage_path": storage_path,
                "original_name": source.name,
                "uploaded_by": self.settings.app_user,
                "content_type": content_type,
                "description": description,
                "status": "pending",
            }
        )
        record_id = record["id"]

        try:
            with source.open("rb") as file_handle:
                self.client.storage.from_(self.settings.bucket).upload(
                    path=storage_path,
                    file=file_handle,
                    file_options={
                        "content-type": content_type,
                        "cache-control": "3600",
                        "upsert": "false",
                    },
                )
        except Exception:
            # The row is only a pending reservation at this point.
            try:
                self._delete_record(record_id)
            finally:
                raise

        try:
            self._invoke_validator(
                {
                    "record_id": record_id,
                    "bucket": self.settings.bucket,
                    "path": storage_path,
                    "mode": "create",
                    "original_name": source.name,
                    "content_type": content_type,
                    "description": description,
                    "uploaded_by": self.settings.app_user,
                }
            )
        except Exception:
            # If the function timed out, it may already have accepted the file.
            # Only clean up while the metadata row still says pending.
            current = self._get_record(record_id)
            if current.get("status") == "pending":
                self._remove_storage_file(self.settings.bucket, storage_path)
                self._update_record(
                    record_id,
                    {
                        "status": "rejected",
                        "validation_error": "Upload validation could not be completed.",
                    },
                )
            raise
        return self._get_record(record_id)

    def download_file(self, record_id: str, output_path: str) -> Path:
        data = self.read_file_bytes(record_id)
        destination = Path(output_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return destination

    def read_file_bytes(self, record_id: str) -> bytes:
        """Read a private object for an in-browser download button."""

        record = self._get_record(record_id)
        return self.client.storage.from_(record["bucket_name"]).download(
            record["storage_path"]
        )

    def create_signed_url(self, record_id: str, expires_in: int = 300) -> str:
        """Create a short-lived download URL without making the bucket public."""

        record = self._get_record(record_id)
        response = self.client.storage.from_(record["bucket_name"]).create_signed_url(
            record["storage_path"],
            expires_in,
            {"download": record["original_name"]},
        )
        signed_url = response.get("signedURL") or response.get("signedUrl")
        if not signed_url:
            raise RuntimeError("Supabase did not return a signed download URL.")
        return signed_url

    def update_metadata(
        self,
        record_id: str,
        *,
        description: str | None = None,
        original_name: str | None = None,
    ) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if description is not None:
            values["description"] = description
        if original_name is not None:
            cleaned = Path(original_name).name.strip()
            if not cleaned:
                raise ValueError("original_name cannot be empty.")
            values["original_name"] = cleaned
        if not values:
            raise ValueError("Provide --description, --name, or use replace.")
        self._get_record(record_id)
        self._update_record(record_id, values)
        return self._get_record(record_id)

    def replace_file(
        self,
        record_id: str,
        local_path: str,
        *,
        description: str | None = None,
        original_name: str | None = None,
    ) -> dict[str, Any]:
        source = Path(local_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"File does not exist: {source}")
        size = source.stat().st_size
        if size > self.settings.max_file_size_bytes:
            raise ValueError(
                f"File is {size} bytes; the configured limit is "
                f"{self.settings.max_file_size_bytes} bytes."
            )

        record = self._get_record(record_id)
        candidate_path = storage_path_for(source.name)
        content_type = content_type_for(source)
        display_name = Path(original_name).name if original_name else source.name
        if not display_name:
            raise ValueError("The replacement file must have a name.")

        with source.open("rb") as file_handle:
            self.client.storage.from_(record["bucket_name"]).upload(
                path=candidate_path,
                file=file_handle,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",
                    "upsert": "false",
                },
            )

        try:
            self._invoke_validator(
                {
                    "record_id": record_id,
                    "bucket": record["bucket_name"],
                    "path": candidate_path,
                    "previous_path": record["storage_path"],
                    "mode": "replace",
                    "original_name": display_name,
                    "content_type": content_type,
                    "description": description,
                    "uploaded_by": self.settings.app_user,
                }
            )
        except Exception:
            # The validator removes rejected candidates. If invocation failed
            # before reaching it, remove the candidate without touching the old file.
            current = self._get_record(record_id)
            if current.get("storage_path") != candidate_path:
                try:
                    self._remove_storage_file(record["bucket_name"], candidate_path)
                except Exception:
                    pass
            raise
        return self._get_record(record_id)

    def delete_file(self, record_id: str) -> None:
        record = self._get_record(record_id)
        self._remove_storage_file(record["bucket_name"], record["storage_path"])
        self._delete_record(record_id)


def jsonable(value: Any) -> str:
    """Format command results consistently for terminal output."""

    return json.dumps(value, indent=2, default=str)
