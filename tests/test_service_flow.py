from types import SimpleNamespace
from uuid import uuid4

from supabase_crud.config import Settings
from supabase_crud.service import FileService


class FakeQuery:
    def __init__(self, client, action="select", values=None):
        self.client = client
        self.action = action
        self.values = values
        self.record_id = None
        self.ordered = False

    def insert(self, values):
        self.action = "insert"
        self.values = values
        return self

    def select(self, _columns):
        return self

    def single(self):
        return self

    def limit(self, _count):
        return self

    def order(self, _column, desc=False):
        self.ordered = desc
        return self

    def eq(self, _column, value):
        self.record_id = value
        return self

    def update(self, values):
        self.action = "update"
        self.values = values
        return self

    def delete(self):
        self.action = "delete"
        return self

    def execute(self):
        if self.action == "insert":
            row = {
                "id": str(uuid4()),
                "created_at": "now",
                "updated_at": "now",
                **self.values,
            }
            self.client.rows.append(row)
            return SimpleNamespace(data=row)
        if self.action == "update":
            row = self.client.find(self.record_id)
            row.update(self.values)
            return SimpleNamespace(data=row)
        if self.action == "delete":
            self.client.rows[:] = [row for row in self.client.rows if row["id"] != self.record_id]
            return SimpleNamespace(data=[])
        rows = self.client.rows
        if self.record_id is not None:
            rows = [row for row in rows if row["id"] == self.record_id]
        if self.ordered:
            rows = list(reversed(rows))
        return SimpleNamespace(data=rows)


class FakeBucket:
    def __init__(self, client):
        self.client = client

    def upload(self, path, file, file_options):
        self.client.objects[path] = file.read()
        self.client.upload_options = file_options
        return {"path": path}

    def remove(self, paths):
        for path in paths:
            self.client.objects.pop(path, None)
        return []

    def download(self, path):
        return self.client.objects[path]


class FakeStorage:
    def __init__(self, client):
        self.client = client

    def from_(self, _bucket):
        return FakeBucket(self.client)


class FakeFunctions:
    def __init__(self, client):
        self.client = client

    def invoke(self, _name, invoke_options):
        payload = invoke_options["body"]
        row = self.client.find(payload["record_id"])
        row.update(
            {
                "status": "active",
                "size_bytes": len(self.client.objects[payload["path"]]),
                "checksum_sha256": "fake-checksum",
            }
        )
        return {"message": "validated"}


class FakeClient:
    def __init__(self):
        self.rows = []
        self.objects = {}
        self.storage = FakeStorage(self)
        self.functions = FakeFunctions(self)

    def table(self, _table_name):
        return FakeQuery(self)

    def find(self, record_id):
        return next(row for row in self.rows if row["id"] == record_id)


def test_create_uploads_bytes_then_calls_validator(tmp_path):
    source = tmp_path / "hello.txt"
    source.write_text("hello from the test", encoding="utf-8")
    fake = FakeClient()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_key="server-key",
        edge_function_secret="function-secret",
    )

    record = FileService(settings, client=fake).create_file(str(source))

    assert record["status"] == "active"
    assert record["size_bytes"] == len(b"hello from the test")
    assert record["storage_path"] in fake.objects
    assert fake.upload_options["content-type"] == "text/plain"


def test_create_file_with_custom_name_and_update_metadata(tmp_path):
    source = tmp_path / "temp_upload.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\n")
    fake = FakeClient()
    settings = Settings(
        supabase_url="https://example.supabase.co",
        supabase_key="server-key",
        edge_function_secret="function-secret",
    )
    service = FileService(settings, client=fake)

    record = service.create_file(
        str(source),
        description="Initial note",
        original_name="architecture_diagram.png",
    )

    assert record["original_name"] == "architecture_diagram.png"
    assert record["description"] == "Initial note"

    # Update metadata (rename and custom field note)
    updated = service.update_metadata(
        record["id"],
        original_name="renamed_diagram.png",
        description="Updated production architecture note",
    )

    assert updated["original_name"] == "renamed_diagram.png"
    assert updated["description"] == "Updated production architecture note"


