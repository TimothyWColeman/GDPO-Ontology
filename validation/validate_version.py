#!/usr/bin/env python3
"""Validate the public GDPO 1.0.0 release identity."""

from __future__ import annotations

import re
from pathlib import Path

from rdflib import DCTERMS, OWL, RDF, XSD, Literal, URIRef

from common import (
    ONTOLOGY,
    ONTOLOGY_IRI,
    RELEASE_DATE,
    ROOT,
    VERSION,
    VERSION_IRI,
    parse_graph,
    relative,
)


EXPECTED_VERSION = "1.0.0"
EXPECTED_LICENSE = URIRef("https://creativecommons.org/licenses/by/4.0/")
EXPECTED_VITSOE_SOURCE = URIRef("https://www.vitsoe.com/us/about/good-design")
STATEMENT_INDIVIDUALS = {
    URIRef(f"https://www.ramsprinciplesofgooddesign.com/GDPO00000{index}")
    for index in range(65, 76)
}


def contains(path: Path, pattern: str) -> bool:
    return path.is_file() and re.search(pattern, path.read_text(encoding="utf-8")) is not None


def main() -> int:
    failures: list[str] = []
    if VERSION != EXPECTED_VERSION:
        failures.append(
            f"VERSION must be {EXPECTED_VERSION} for this public baseline, found {VERSION!r}"
        )
    if ONTOLOGY.name != f"gdpo-{VERSION}.ttl" or not ONTOLOGY.is_file():
        failures.append(f"canonical ontology is missing: {relative(ONTOLOGY)}")
        graph = None
    else:
        graph = parse_graph(ONTOLOGY)

    active_ontologies = sorted((ROOT / "ontology").glob("gdpo-*.ttl"))
    if active_ontologies != [ONTOLOGY]:
        failures.append(
            "ontology/ must expose exactly one canonical gdpo-*.ttl file; found "
            + ", ".join(relative(path) for path in active_ontologies)
        )

    if graph is not None:
        if (ONTOLOGY_IRI, RDF.type, OWL.Ontology) not in graph:
            failures.append("canonical ontology declaration is absent")
        version_iris = set(graph.objects(ONTOLOGY_IRI, OWL.versionIRI))
        if version_iris != {VERSION_IRI}:
            failures.append(
                f"owl:versionIRI must be {VERSION_IRI}; found {sorted(map(str, version_iris))}"
            )
        if set(graph.objects(ONTOLOGY_IRI, OWL.priorVersion)):
            failures.append("the public baseline must not expose owl:priorVersion")
        version_infos = [str(value) for value in graph.objects(ONTOLOGY_IRI, OWL.versionInfo)]
        if len(version_infos) != 1 or f"Version {VERSION}" not in version_infos[0]:
            failures.append(f"owl:versionInfo must singularly identify Version {VERSION}")
        expected_date = Literal(RELEASE_DATE, datatype=XSD.date)
        for predicate, name in ((DCTERMS.issued, "issued"), (DCTERMS.modified, "modified")):
            if set(graph.objects(ONTOLOGY_IRI, predicate)) != {expected_date}:
                failures.append(
                    f"dcterms:{name} must be {RELEASE_DATE}^^xsd:date"
                )
        if set(graph.objects(ONTOLOGY_IRI, DCTERMS.license)) != {EXPECTED_LICENSE}:
            failures.append("dcterms:license must identify CC BY 4.0")
        if set(graph.objects(ONTOLOGY_IRI, DCTERMS.source)) != {EXPECTED_VITSOE_SOURCE}:
            failures.append("dcterms:source must identify the public Rams-principles source")
        for statement in sorted(STATEMENT_INDIVIDUALS):
            statement_sources = set(graph.objects(statement, DCTERMS.source))
            if statement_sources != {EXPECTED_VITSOE_SOURCE}:
                failures.append(
                    f"canonical statement/specification lacks Vitsœ provenance: {statement}"
                )

    text_contracts = [
        (ROOT / "README.md", rf"v?{re.escape(VERSION)}"),
        (ROOT / "CHANGELOG.md", rf"\[{re.escape(VERSION)}\]|v{re.escape(VERSION)}"),
        (ROOT / "CITATION.cff", rf"(?m)^version:\s*['\"]?{re.escape(VERSION)}['\"]?\s*$"),
        (ROOT / f"RELEASE_NOTES_v{VERSION}.md", rf"v{re.escape(VERSION)}"),
    ]
    for path, pattern in text_contracts:
        if not path.is_file():
            failures.append(f"required public release file is missing: {relative(path)}")
        elif not contains(path, pattern):
            failures.append(f"{relative(path)} is not synchronized to v{VERSION}")

    if failures:
        print("FAIL: public release identity synchronization")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "PASS: public release identity synchronization "
        f"({VERSION}; {VERSION_IRI}; issued {RELEASE_DATE})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
