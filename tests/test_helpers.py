from pathlib import Path

from supabase_crud.helpers import (
    content_type_for,
    human_size,
    is_safe_storage_path,
    storage_path_for,
)


def test_storage_path_is_unique_and_confined_to_uploads():
    first = storage_path_for("my résumé (final).pdf")
    second = storage_path_for("my résumé (final).pdf")

    assert first.startswith("uploads/")
    assert first != second
    assert " " not in first
    assert is_safe_storage_path(first)


def test_storage_path_rejects_traversal_and_absolute_paths():
    assert not is_safe_storage_path("../secret.txt")
    assert not is_safe_storage_path("/absolute.txt")
    assert not is_safe_storage_path("uploads\\secret.txt")
    assert is_safe_storage_path("uploads/file.txt")


def test_content_type_and_human_size():
    assert content_type_for(Path("notes.txt")) == "text/plain"
    assert content_type_for(Path("records.csv")) == "text/csv"
    assert content_type_for(Path("metadata.json")) == "application/json"
    assert human_size(1024 * 1024) == "1.0 MB"
    assert human_size(None) == "unknown"
