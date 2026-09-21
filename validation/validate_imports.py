#!/usr/bin/env python3
"""Validate the checksum-verified, catalog-resolved offline import closure."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from rdflib import Graph, OWL, RDF, RDFS, URIRef

from common import (
    CATALOG,
    IMPORT_LOCK,
    ONTOLOGY,
    ONTOLOGY_IRI,
    ROOT,
    VERSION,
    VERSION_IRI,
    LOCAL_BASE,
    parse_graph,
    relative,
    sha256,
)


EXPECTED_DIRECT_IMPORTS = {
    URIRef("http://purl.obolibrary.org/obo/bfo/2020/bfo.owl"),
    URIRef("https://www.commoncoreontologies.org/2024-11-05/AgentOntology"),
    URIRef("https://www.commoncoreontologies.org/2024-11-06/ArtifactOntology"),
}
LOCAL_ENTITY = re.compile(re.escape(LOCAL_BASE) + r"GDPO[0-9]{7}$")
BFO_ENTITY = re.compile(r"http://purl\.obolibrary\.org/obo/BFO_[0-9]{7}$")
CCO_ENTITY = re.compile(r"https://www\.commoncoreontologies\.org/ont[0-9]{8}$")
DECLARATION_TYPES = {
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
    OWL.NamedIndividual,
    RDFS.Datatype,
}


def catalog_mappings() -> dict[str, Path]:
    tree = ET.parse(CATALOG)
    namespace = {"c": "urn:oasis:names:tc:entity:xmlns:xml:catalog"}
    mappings: dict[str, Path] = {}
    for element in tree.findall("c:uri", namespace):
        name = element.attrib.get("name")
        target = element.attrib.get("uri")
        if not name or not target:
            raise ValueError("catalog uri entries require both name and uri")
        if name in mappings:
            raise ValueError(f"duplicate catalog mapping: {name}")
        if "://" in target or Path(target).is_absolute():
            raise ValueError(f"catalog target must be a repository-relative local path: {target}")
        target_path = (CATALOG.parent / target).resolve()
        try:
            target_path.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"catalog target escapes repository: {target}") from exc
        if not target_path.is_file():
            raise ValueError(f"catalog target does not exist: {target}")
        mappings[name] = target_path
    return mappings


def main() -> int:
    failures: list[str] = []
    referenced_entities: set[URIRef] = set()
    try:
        lock = json.loads(IMPORT_LOCK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: import lock is unreadable: {exc}", file=sys.stderr)
        return 1

    if lock.get("schema_version") != "1.0":
        failures.append("import lock schema_version must be 1.0")
    if lock.get("ontology_release") != VERSION:
        failures.append("import lock ontology_release does not match VERSION")

    try:
        mappings = catalog_mappings()
    except (OSError, ET.ParseError, ValueError) as exc:
        failures.append(f"catalog validation failed: {exc}")
        mappings = {}

    expected_self = {
        str(ONTOLOGY_IRI): ONTOLOGY.resolve(),
        str(VERSION_IRI): ONTOLOGY.resolve(),
    }
    for iri, expected_path in expected_self.items():
        if mappings.get(iri) != expected_path:
            failures.append(
                f"catalog self mapping for {iri} must resolve to {relative(ONTOLOGY)}"
            )
    artifacts = lock.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        failures.append("import lock artifacts must be a non-empty list")
        artifacts = []

    locked_paths: set[Path] = set()
    iri_to_path: dict[str, Path] = {}
    declaration_graph = Graph()
    for index, record in enumerate(artifacts, start=1):
        if not isinstance(record, dict):
            failures.append(f"import artifact {index} is not an object")
            continue
        try:
            path = (ROOT / record["path"]).resolve()
            expected_hash = record["sha256"]
            ontology_iri = record["ontology_iri"]
            version_iri = record["version_iri"]
            source_url = record["source_url"]
        except KeyError as exc:
            failures.append(f"import artifact {index} lacks {exc.args[0]}")
            continue
        if path in locked_paths:
            failures.append(f"duplicate import-lock path: {record['path']}")
            continue
        locked_paths.add(path)
        if not path.is_file():
            failures.append(f"locked import is missing: {record['path']}")
            continue
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            failures.append(f"invalid SHA-256 contract for {record['path']}")
        elif (actual_hash := sha256(path)) != expected_hash:
            failures.append(
                f"checksum mismatch for {record['path']}: {actual_hash} != {expected_hash}"
            )
        if not str(source_url).startswith("https://"):
            failures.append(f"source_url is not HTTPS for {record['path']}")

        try:
            graph = parse_graph(path)
        except Exception as exc:  # pragma: no cover - parser diagnostic path
            failures.append(f"cannot parse {record['path']}: {exc}")
            continue
        declaration_graph += graph
        ontology_node = URIRef(ontology_iri)
        if (ontology_node, RDF.type, OWL.Ontology) not in graph:
            failures.append(
                f"{record['path']} does not declare locked ontology IRI {ontology_iri}"
            )
        version_values = set(graph.objects(ontology_node, OWL.versionIRI))
        if version_values != {URIRef(version_iri)}:
            failures.append(
                f"{record['path']} versionIRI mismatch: {sorted(map(str, version_values))}"
            )
        iri_to_path[ontology_iri] = path
        iri_to_path[version_iri] = path
        for iri in (ontology_iri, version_iri):
            if mappings.get(iri) != path:
                failures.append(
                    f"catalog does not map locked IRI {iri} to {record['path']}"
                )

    actual_import_files = {
        path.resolve()
        for path in (ROOT / "imports").iterdir()
        if path.is_file() and path.suffix.lower() in {".owl", ".ttl", ".rdf"}
    }
    if actual_import_files != locked_paths:
        missing = sorted(relative(path) for path in locked_paths - actual_import_files)
        unlocked = sorted(relative(path) for path in actual_import_files - locked_paths)
        if missing:
            failures.append("locked imports absent from directory: " + ", ".join(missing))
        if unlocked:
            failures.append("unlocked import snapshots present: " + ", ".join(unlocked))

    try:
        ontology_graph = parse_graph(ONTOLOGY)
    except Exception as exc:
        failures.append(f"cannot parse canonical ontology: {exc}")
        ontology_graph = None
    if ontology_graph is not None:
        declaration_graph += ontology_graph
        direct_imports = set(ontology_graph.objects(ONTOLOGY_IRI, OWL.imports))
        if direct_imports != EXPECTED_DIRECT_IMPORTS:
            failures.append(
                "direct imports differ from the governed GDPO contract: "
                f"{sorted(map(str, direct_imports))}"
            )

        reachable_files: set[Path] = set()
        pending = list(direct_imports)
        visited_iris: set[URIRef] = set()
        while pending:
            import_iri = pending.pop()
            if import_iri in visited_iris:
                continue
            visited_iris.add(import_iri)
            path = mappings.get(str(import_iri))
            if path is None:
                failures.append(f"unmapped import edge: {import_iri}")
                continue
            if path not in locked_paths:
                failures.append(f"import edge resolves outside locked closure: {import_iri}")
                continue
            reachable_files.add(path)
            try:
                imported_graph = parse_graph(path)
            except Exception:
                continue
            pending.extend(imported_graph.objects(None, OWL.imports))

        if reachable_files != locked_paths:
            unreachable = sorted(relative(path) for path in locked_paths - reachable_files)
            failures.append(
                "import lock contains files outside the reachable closure: "
                + ", ".join(unreachable)
            )

        referenced_entities = {
            term
            for triple in ontology_graph
            for term in triple
            if isinstance(term, URIRef)
            and (
                LOCAL_ENTITY.fullmatch(str(term))
                or BFO_ENTITY.fullmatch(str(term))
                or CCO_ENTITY.fullmatch(str(term))
            )
        }
        undefined = {
            term
            for term in referenced_entities
            if not any(
                (term, RDF.type, declaration_type) in declaration_graph
                for declaration_type in DECLARATION_TYPES
            )
        }
        if undefined:
            failures.append(
                "GDPO/BFO/CCO entity references lack declarations in the authored "
                "graph or locked closure: "
                + ", ".join(sorted(map(str, undefined)))
            )

    if failures:
        print("FAIL: offline import closure")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "PASS: offline import closure "
        f"({len(locked_paths)} checksum-verified artifacts; "
        f"{len(mappings)} catalog mappings; {len(referenced_entities)} referenced "
        "GDPO/BFO/CCO entities owned; no network resolution required)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
