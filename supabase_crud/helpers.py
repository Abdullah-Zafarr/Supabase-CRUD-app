"""Small pure helpers shared by the CLI and service layer."""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from uuid import uuid4


KNOWN_MIME_TYPES = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def content_type_for(path: Path) -> str:
    """Return a useful upload content type, with a safe binary fallback."""

    ext = path.suffix.lower()
    if ext in KNOWN_MIME_TYPES:
        return KNOWN_MIME_TYPES[ext]
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def storage_path_for(filename: str) -> str:
    """Build a safe, collision-resistant path under the uploads prefix."""

    name = Path(filename).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._")
    safe_name = safe_name[:100] or "file"
    return f"uploads/{uuid4().hex}_{safe_name}"


def is_safe_storage_path(path: str) -> bool:
    """Reject traversal and absolute paths before any Storage operation."""

    if not path or path.startswith("/") or "\\" in path:
        return False
    parts = path.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def human_size(size: int | None) -> str:
    if size is None:
        return "unknown"
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"

