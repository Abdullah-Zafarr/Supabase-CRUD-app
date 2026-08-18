"""Command-line interface for the Supabase file CRUD app."""

from __future__ import annotations

import argparse
import sys

from .config import ConfigurationError, Settings
from .service import FileService, jsonable


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="supabase-files",
        description="CRUD for Supabase Storage files and public.file_records metadata.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="Upload a file and validate it server-side.")
    create.add_argument("file", help="Local file to upload")
    create.add_argument("--description", help="Optional metadata description")

    commands.add_parser("list", help="List file metadata records.")

    read = commands.add_parser("read", help="Read one file's metadata.")
    read.add_argument("record_id")

    download = commands.add_parser("download", help="Download a stored file.")
    download.add_argument("record_id")
    download.add_argument("output", help="Local output path")

    update = commands.add_parser("update", help="Update metadata without replacing bytes.")
    update.add_argument("record_id")
    update.add_argument("--description")
    update.add_argument("--name", help="Display/original filename")

    replace = commands.add_parser("replace", help="Replace bytes and re-run Edge validation.")
    replace.add_argument("record_id")
    replace.add_argument("file", help="Replacement local file")
    replace.add_argument("--description")
    replace.add_argument("--name", help="Display/original filename")

    delete = commands.add_parser("delete", help="Delete Storage object and metadata row.")
    delete.add_argument("record_id")
    return parser


def run(args: argparse.Namespace, service: FileService) -> object:
    if args.command == "create":
        return service.create_file(args.file, args.description)
    if args.command == "list":
        return service.list_files()
    if args.command == "read":
        return service.get_file(args.record_id)
    if args.command == "download":
        return {"downloaded_to": str(service.download_file(args.record_id, args.output))}
    if args.command == "update":
        return service.update_metadata(
            args.record_id, description=args.description, original_name=args.name
        )
    if args.command == "replace":
        return service.replace_file(
            args.record_id,
            args.file,
            description=args.description,
            original_name=args.name,
        )
    if args.command == "delete":
        service.delete_file(args.record_id)
        return {"deleted": args.record_id}
    raise ValueError(f"Unknown command: {args.command}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        service = FileService(Settings.from_env())
        print(jsonable(run(args, service)))
    except (ConfigurationError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except Exception as exc:  # SDK errors include useful provider messages.
        print(f"Supabase error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

