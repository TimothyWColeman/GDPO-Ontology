#!/usr/bin/env python3
"""Build and verify a deterministic public GDPO release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote

from rdflib import DCTERMS, OWL, Graph, URIRef


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
ONTOLOGY = ROOT / "ontology" / f"gdpo-{VERSION}.ttl"
ONTOLOGY_IRI = URIRef(
    "https://www.ramsprinciplesofgooddesign.com/GoodDesignPrinciplesOntology"
)
ARCHIVE_BASENAME = f"gdpo-v{VERSION}"
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files_under(directory: str, suffixes: set[str]) -> set[Path]:
    base = ROOT / directory
    return {
        path
        for path in base.rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes
    }


def release_files() -> list[Path]:
    required = {
        ROOT / name
        for name in (
            "README.md",
            "CHANGELOG.md",
            "CITATION.cff",
            "LICENSE",
            "NOTICE",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "VERSION",
            "requirements.txt",
            ".gitignore",
            f"RELEASE_NOTES_v{VERSION}.md",
            "ontology/catalog-v001.xml",
            f"ontology/gdpo-{VERSION}.ttl",
            "imports/import-lock.json",
            "scripts/build_release.py",
            ".github/workflows/validate.yml",
        )
    }
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("required public release inputs are missing: " + ", ".join(missing))
    paths = set(required)
    paths.update(files_under("docs", {".md", ".svg"}))
    paths.update(files_under("examples", {".md", ".ttl"}))
    paths.update(files_under("imports", {".md", ".json", ".owl", ".ttl"}))
    paths.update(files_under("queries", {".md", ".json", ".rq"}))
    paths.update(files_under("shapes", {".md", ".ttl"}))
    paths.update(files_under("validation", {".csv", ".md", ".py", ".ttl"}))
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def ontology_metadata() -> tuple[str, str]:
    graph = Graph().parse(ONTOLOGY)
    version_iris = {str(value) for value in graph.objects(ONTOLOGY_IRI, OWL.versionIRI)}
    dates = {str(value) for value in graph.objects(ONTOLOGY_IRI, DCTERMS.issued)}
    if len(version_iris) != 1 or len(dates) != 1:
        raise ValueError("ontology must expose one version IRI and one issued date")
    return next(iter(version_iris)), next(iter(dates))


def validate_packaged_links(files: list[Path]) -> None:
    packaged = {path.relative_to(ROOT).as_posix() for path in files}
    directories = {
        parent.as_posix()
        for name in packaged
        for parent in Path(name).parents
        if parent.as_posix() != "."
    }
    failures: list[str] = []
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        source = path.relative_to(ROOT).as_posix()
        for line in path.read_text(encoding="utf-8").splitlines():
            for raw_target in _markdown_targets(line):
                target = raw_target.strip().strip("<>").split("#", 1)[0]
                if not target or "://" in target or target.startswith(("mailto:", "#")):
                    continue
                resolved = posixpath.normpath(
                    posixpath.join(posixpath.dirname(source), unquote(target))
                ).rstrip("/")
                if resolved not in packaged and resolved not in directories:
                    failures.append(f"{source} -> {target}")
    if failures:
        raise ValueError("release package has unresolved local Markdown links: " + ", ".join(sorted(failures)))


def _markdown_targets(line: str) -> list[str]:
    targets: list[str] = []
    start = 0
    while True:
        open_paren = line.find("](", start)
        if open_paren < 0:
            return targets
        close_paren = line.find(")", open_paren + 2)
        if close_paren < 0:
            return targets
        targets.append(line[open_paren + 2 : close_paren])
        start = close_paren + 1


def manifest(files: list[Path]) -> dict:
    version_iri, release_date = ontology_metadata()
    entries = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": len(path.read_bytes()),
            "sha256": sha256_bytes(path.read_bytes()),
        }
        for path in files
    ]
    return {
        "schema_version": "1.0",
        "name": "Good Design Principles Ontology",
        "version": VERSION,
        "ontology_iri": str(ONTOLOGY_IRI),
        "version_iri": version_iri,
        "release_date": release_date,
        "entries": entries,
    }


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def build(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = release_files()
    validate_packaged_links(files)
    release_manifest = manifest(files)
    manifest_bytes = (
        json.dumps(release_manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    ).encode("utf-8")
    sums = [f"{entry['sha256']}  {entry['path']}" for entry in release_manifest["entries"]]
    sums.append(f"{sha256_bytes(manifest_bytes)}  MANIFEST.json")
    sums_bytes = ("\n".join(sums) + "\n").encode("utf-8")
    archive = output_dir / f"{ARCHIVE_BASENAME}.zip"
    prefix = f"{ARCHIVE_BASENAME}/"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            bundle.writestr(
                zip_info(prefix + path.relative_to(ROOT).as_posix()),
                path.read_bytes(),
                compresslevel=9,
            )
        bundle.writestr(zip_info(prefix + "MANIFEST.json"), manifest_bytes, compresslevel=9)
        bundle.writestr(zip_info(prefix + "SHA256SUMS"), sums_bytes, compresslevel=9)
    archive_hash = sha256_bytes(archive.read_bytes())
    checksum = output_dir / f"{ARCHIVE_BASENAME}.zip.sha256"
    checksum.write_text(f"{archive_hash}  {archive.name}\n", encoding="utf-8", newline="\n")
    outer_manifest = output_dir / "release-manifest.json"
    outer_manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "release": release_manifest,
                "archive": {"filename": archive.name, "bytes": len(archive.read_bytes()), "sha256": archive_hash},
                "checksum_file": checksum.name,
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return [archive, checksum, outer_manifest]


def verify(outputs: list[Path]) -> None:
    archive, checksum, outer_manifest = outputs
    archive_hash = sha256_bytes(archive.read_bytes())
    if checksum.read_text(encoding="utf-8") != f"{archive_hash}  {archive.name}\n":
        raise ValueError("archive checksum is invalid")
    outer = json.loads(outer_manifest.read_text(encoding="utf-8"))
    if outer["archive"]["sha256"] != archive_hash:
        raise ValueError("outer manifest archive checksum is invalid")
    prefix = f"{ARCHIVE_BASENAME}/"
    with zipfile.ZipFile(archive) as bundle:
        if any(info.date_time != FIXED_TIMESTAMP for info in bundle.infolist()):
            raise ValueError("archive contains a non-deterministic timestamp")
        expected = {
            prefix + entry["path"] for entry in outer["release"]["entries"]
        } | {prefix + "MANIFEST.json", prefix + "SHA256SUMS"}
        if {info.filename for info in bundle.infolist()} != expected:
            raise ValueError("archive member inventory differs from its manifest")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify byte-for-byte deterministic output")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        if args.check:
            with tempfile.TemporaryDirectory(prefix="gdpo-release-a-") as first, tempfile.TemporaryDirectory(prefix="gdpo-release-b-") as second:
                first_outputs = build(Path(first))
                second_outputs = build(Path(second))
                verify(first_outputs)
                verify(second_outputs)
                for first_path, second_path in zip(first_outputs, second_outputs, strict=True):
                    if first_path.name != second_path.name or first_path.read_bytes() != second_path.read_bytes():
                        raise ValueError(f"release output is not deterministic: {first_path.name}")
                print(f"PASS: deterministic public release build ({first_outputs[0].name})")
        else:
            outputs = build(args.output_dir)
            verify(outputs)
            for path in outputs:
                try:
                    display_path = path.relative_to(ROOT)
                except ValueError:
                    display_path = path
                print(f"BUILT: {display_path}")
        return 0
    except Exception as exc:
        print(f"FAIL: release build: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
