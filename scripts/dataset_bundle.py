#!/usr/bin/env python3
"""Pack, verify, and restore private PhishGate experiment datasets.

Archives retain repository-relative paths so they can be restored directly into
a Docker-free Conda checkout. Existing files are accepted only when their
contents are identical; this command never silently overwrites dataset files.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_DIRECTORY = ROOT / "tmp" / "dataset-bundles"
SCHEMA_VERSION = 1
BUFFER_SIZE = 1024 * 1024


@dataclass(frozen=True)
class Group:
    archive: str
    paths: tuple[str, ...]
    count_root: str


GROUPS: dict[str, Group] = {
    "phishdecloaker": Group(
        archive="G1-phishdecloaker.tar.gz",
        paths=("data/private/phishdecloaker/extracted/src",),
        count_root="data/private/phishdecloaker/extracted/src",
    ),
    "dynapd": Group(
        archive="G1-dynapd-selected.tar.gz",
        paths=(
            "data/private/dynapd/selection.csv",
            "data/private/dynapd/raw_selected",
        ),
        count_root="data/private/dynapd/raw_selected",
    ),
    "manual-phishing": Group(
        archive="G2-manual-phishing.tar.gz",
        paths=(
            "data/manual_annotation.csv",
            "data/manual/samples/phishing",
        ),
        count_root="data/manual/samples/phishing",
    ),
    "manual-benign": Group(
        archive="G3-manual-benign.tar.gz",
        paths=(
            "data/manual_benign_annotation.csv",
            "data/manual/samples/benign",
        ),
        count_root="data/manual/samples/benign",
    ),
}

# normalized_tarinfo() deliberately strips real permission bits for
# reproducible archives (every directory becomes 0o755), but some kits' own
# PHP refuses to run unless specific directories are exactly 0o777 -- they
# copy themselves into <that dir>/<md5>/ on every visit (see
# docker-compose.yaml's matching tmpfs mode=0o777 for PhishDecloaker's kit4).
# restore_archive() chmods these specific directories back to 0o777 after
# extraction so a transferred bundle behaves the same as a direct ZIP
# extraction, which keeps the archive's original mode.
WORLD_WRITABLE_DIRECTORIES = (
    "data/private/phishdecloaker/extracted/src/kit4/a1b2c3",
    "data/private/phishdecloaker/extracted/src/kit4/iplogs",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(BUFFER_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_payload(root: Path, relative_paths: Iterable[str]) -> Iterable[tuple[Path, str]]:
    """Yield directories and regular files in stable archive order."""

    for relative in relative_paths:
        source = root / relative
        if not source.exists():
            raise SystemExit(f"Required dataset path is missing: {source}")
        candidates = (source,) if source.is_file() else (source, *sorted(source.rglob("*")))
        for candidate in candidates:
            if candidate.is_symlink():
                raise SystemExit(f"Dataset bundles do not permit symbolic links: {candidate}")
            if not candidate.is_dir() and not candidate.is_file():
                raise SystemExit(f"Unsupported dataset filesystem entry: {candidate}")
            yield candidate, candidate.relative_to(root).as_posix()


def normalized_tarinfo(source: Path, archive_name: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(archive_name + ("/" if source.is_dir() else ""))
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    if source.is_dir():
        info.type = tarfile.DIRTYPE
        info.mode = 0o755
    else:
        info.type = tarfile.REGTYPE
        info.mode = 0o644
        info.size = source.stat().st_size
    return info


def write_archive(root: Path, destination: Path, group: Group) -> tuple[int, int]:
    file_count = 0
    directory_count = 0
    with destination.open("wb") as raw_output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_output, mtime=0) as compressed:
            with tarfile.open(mode="w", fileobj=compressed, format=tarfile.PAX_FORMAT) as archive:
                for source, archive_name in iter_payload(root, group.paths):
                    info = normalized_tarinfo(source, archive_name)
                    if source.is_dir():
                        archive.addfile(info)
                        directory_count += 1
                    else:
                        with source.open("rb") as content:
                            archive.addfile(info, content)
                        file_count += 1
    return file_count, directory_count


def top_level_directory_count(root: Path, relative: str) -> int:
    directory = root / relative
    return sum(1 for child in directory.iterdir() if child.is_dir())


def validate_dynapd_selection(root: Path) -> None:
    selection = root / "data/private/dynapd/selection.csv"
    raw_selected = root / "data/private/dynapd/raw_selected"
    if not selection.is_file() or not raw_selected.is_dir():
        raise SystemExit("DynaPD requires selection.csv and raw_selected/.")
    with selection.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    selected = {row.get("copied_directory", "").strip() for row in rows}
    selected.discard("")
    present = {child.name for child in raw_selected.iterdir() if child.is_dir()}
    if len(rows) != 100 or len(selected) != 100:
        raise SystemExit(
            f"DynaPD selection must contain 100 unique copied directories; "
            f"found {len(rows)} rows and {len(selected)} unique directories."
        )
    if selected != present:
        missing = sorted(selected - present)
        extra = sorted(present - selected)
        raise SystemExit(
            "DynaPD selection.csv and raw_selected/ differ "
            f"(missing={missing[:5]}, extra={extra[:5]})."
        )


def pack(root: Path, output: Path, selected_groups: list[str]) -> None:
    if len(selected_groups) != len(set(selected_groups)):
        raise SystemExit("Each dataset group may be selected only once.")
    output.mkdir(parents=True, exist_ok=True)
    if "dynapd" in selected_groups:
        validate_dynapd_selection(root)

    planned = [output / GROUPS[name].archive for name in selected_groups]
    planned += [output / "manifest.json", output / "SHA256SUMS"]
    conflicts = [path for path in planned if path.exists()]
    if conflicts:
        raise SystemExit(f"Refusing to overwrite existing bundle output: {conflicts[0]}")

    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "groups": {},
    }
    checksums: list[str] = []
    with tempfile.TemporaryDirectory(prefix="phishgate-bundle-", dir=output) as temporary:
        temporary_root = Path(temporary)
        for name in selected_groups:
            group = GROUPS[name]
            temporary_archive = temporary_root / group.archive
            file_count, directory_count = write_archive(root, temporary_archive, group)
            digest = sha256_file(temporary_archive)
            archive_size = temporary_archive.stat().st_size
            cohort_count = top_level_directory_count(root, group.count_root)
            manifest["groups"][name] = {  # type: ignore[index]
                "archive": group.archive,
                "sha256": digest,
                "archive_bytes": archive_size,
                "cohort_count": cohort_count,
                "file_count": file_count,
                "directory_count": directory_count,
                "paths": list(group.paths),
            }
            checksums.append(f"{digest}  {group.archive}\n")
            os.replace(temporary_archive, output / group.archive)

    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "SHA256SUMS").write_text("".join(checksums), encoding="utf-8")
    print(f"Created {len(selected_groups)} dataset bundle(s) in {output}")
    for name in selected_groups:
        details = manifest["groups"][name]  # type: ignore[index]
        print(f"  {name}: {details['cohort_count']} items -> {details['archive']}")


def load_manifest(input_directory: Path) -> dict[str, object]:
    path = input_directory / "manifest.json"
    if not path.is_file():
        raise SystemExit(f"Bundle manifest is missing: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit(f"Unsupported dataset bundle schema: {manifest.get('schema_version')!r}")
    if not isinstance(manifest.get("groups"), dict):
        raise SystemExit("Dataset bundle manifest has no groups object.")
    return manifest


def selected_manifest_groups(
    manifest: dict[str, object], requested: list[str] | None
) -> list[tuple[str, dict[str, object]]]:
    manifest_groups = manifest["groups"]
    assert isinstance(manifest_groups, dict)
    names = requested or list(manifest_groups)
    result: list[tuple[str, dict[str, object]]] = []
    for name in names:
        if name not in GROUPS or name not in manifest_groups:
            raise SystemExit(f"Dataset group is not present in this bundle: {name}")
        details = manifest_groups[name]
        if not isinstance(details, dict):
            raise SystemExit(f"Invalid manifest entry for dataset group: {name}")
        result.append((name, details))
    return result


def verify(input_directory: Path, requested: list[str] | None = None) -> dict[str, object]:
    manifest = load_manifest(input_directory)
    for name, details in selected_manifest_groups(manifest, requested):
        archive_name = details.get("archive")
        expected = details.get("sha256")
        if not isinstance(archive_name, str) or not isinstance(expected, str):
            raise SystemExit(f"Invalid archive metadata for dataset group: {name}")
        archive = input_directory / archive_name
        if not archive.is_file():
            raise SystemExit(f"Dataset archive is missing: {archive}")
        actual = sha256_file(archive)
        if actual != expected:
            raise SystemExit(f"SHA-256 mismatch for {archive.name}: expected {expected}, got {actual}")
        print(f"Verified {name}: {archive.name}")
    return manifest


def safe_member_path(member: tarfile.TarInfo, allowed_paths: tuple[str, ...]) -> PurePosixPath:
    path = PurePosixPath(member.name)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"Unsafe path in dataset archive: {member.name}")
    if not member.isdir() and not member.isreg():
        raise SystemExit(f"Links and special files are not allowed in dataset archive: {member.name}")
    value = path.as_posix().rstrip("/")
    if not any(value == allowed or value.startswith(allowed.rstrip("/") + "/") for allowed in allowed_paths):
        raise SystemExit(f"Unexpected path in dataset archive: {member.name}")
    return path


def safe_target(root: Path, relative: PurePosixPath) -> Path:
    target = root.joinpath(*relative.parts)
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise SystemExit(f"Dataset archive path escapes the project root: {relative}") from error
    if target.is_symlink():
        raise SystemExit(f"Refusing to restore through an existing symbolic link: {target}")
    return target


def streams_equal(left: BinaryIO, right: BinaryIO) -> bool:
    while True:
        left_chunk = left.read(BUFFER_SIZE)
        right_chunk = right.read(BUFFER_SIZE)
        if left_chunk != right_chunk:
            return False
        if not left_chunk:
            return True


def preflight_archive(root: Path, archive_path: Path, group: Group) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive:
            relative = safe_member_path(member, group.paths)
            target = safe_target(root, relative)
            if member.isdir():
                if target.exists() and not target.is_dir():
                    raise SystemExit(f"Existing path conflicts with bundle directory: {target}")
                continue
            if not target.exists():
                continue
            if not target.is_file() or target.stat().st_size != member.size:
                raise SystemExit(f"Refusing to overwrite different dataset file: {target}")
            bundled = archive.extractfile(member)
            if bundled is None:
                raise SystemExit(f"Could not read bundled file: {member.name}")
            with bundled, target.open("rb") as existing:
                if not streams_equal(bundled, existing):
                    raise SystemExit(f"Refusing to overwrite different dataset file: {target}")


def restore_archive(root: Path, archive_path: Path, group: Group) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive:
            relative = safe_member_path(member, group.paths)
            target = safe_target(root, relative)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                if relative.as_posix() in WORLD_WRITABLE_DIRECTORIES:
                    target.chmod(0o777)
                continue
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            bundled = archive.extractfile(member)
            if bundled is None:
                raise SystemExit(f"Could not read bundled file: {member.name}")
            try:
                with bundled, target.open("xb") as destination:
                    shutil.copyfileobj(bundled, destination, length=BUFFER_SIZE)
            except Exception:
                target.unlink(missing_ok=True)
                raise
            target.chmod(0o644)


def unpack(root: Path, input_directory: Path, requested: list[str] | None) -> None:
    manifest = verify(input_directory, requested)
    groups = selected_manifest_groups(manifest, requested)
    for name, details in groups:
        archive_name = details["archive"]
        assert isinstance(archive_name, str)
        preflight_archive(root, input_directory / archive_name, GROUPS[name])
    for name, details in groups:
        archive_name = details["archive"]
        assert isinstance(archive_name, str)
        restore_archive(root, input_directory / archive_name, GROUPS[name])
        print(f"Restored {name} into {root}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help=argparse.SUPPRESS,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    pack_parser = subparsers.add_parser("pack", help="create private dataset archives")
    pack_parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_BUNDLE_DIRECTORY,
        help="bundle directory (default: PhishGate/tmp/dataset-bundles)",
    )
    pack_parser.add_argument(
        "--groups", nargs="+", choices=tuple(GROUPS), default=list(GROUPS)
    )

    for command, help_text in (
        ("verify", "verify archive checksums"),
        ("unpack", "verify and safely restore archives"),
    ):
        command_parser = subparsers.add_parser(command, help=help_text)
        command_parser.add_argument(
            "--input",
            type=Path,
            default=DEFAULT_BUNDLE_DIRECTORY,
            help="bundle directory (default: PhishGate/tmp/dataset-bundles)",
        )
        command_parser.add_argument("--groups", nargs="+", choices=tuple(GROUPS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    if args.command == "pack":
        pack(root, args.output.resolve(), args.groups)
    elif args.command == "verify":
        verify(args.input.resolve(), args.groups)
    else:
        unpack(root, args.input.resolve(), args.groups)


if __name__ == "__main__":
    main()
