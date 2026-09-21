#!/usr/bin/env python3
"""Validate the GDPO SHACL profile against positive and negative proof fixtures."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, RDF
from rdflib.namespace import SH

from common import ONTOLOGY, ROOT, parse_graph, relative


SHAPES = ROOT / "shapes" / "gdpo-shapes.ttl"
FIXTURES = ROOT / "validation" / "fixtures"
MANIFEST = ROOT / "validation" / "fixture-manifest.csv"
CODE = re.compile(r"\[([A-Z0-9-]+)\]")


def contracted_results(results_graph: Graph) -> set[tuple[str, str, str]]:
    contracted = set()
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        focus = results_graph.value(result, SH.focusNode)
        message = results_graph.value(result, SH.resultMessage)
        severity = results_graph.value(result, SH.resultSeverity)
        match = CODE.search(str(message)) if message is not None else None
        code = match.group(1) if match else "MISSING-CODE"
        severity_name = str(severity).rsplit("#", 1)[-1] if severity else "None"
        contracted.add((str(focus), code, severity_name))
    return contracted


def main() -> int:
    shapes = parse_graph(SHAPES)
    # The profile needs GDPO's local subclass graph. Import integrity and the full
    # external closure are governed separately by validate_imports.py and ROBOT;
    # excluding the large import graphs keeps focused SHACL runs deterministic.
    ontology = parse_graph(ONTOLOGY)
    expected: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    expected_conformance: dict[str, bool] = {}
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            filename = row["fixture"]
            conforms = row["expected_conforms"].lower() == "true"
            if filename in expected_conformance and expected_conformance[filename] != conforms:
                raise ValueError(f"conflicting conformance contract for {filename}")
            expected_conformance[filename] = conforms
            if row["focus_node"]:
                expected[filename].add(
                    (row["focus_node"], row["expected_code"], row["severity"])
                )

    fixture_files = {path.name for path in FIXTURES.glob("*.ttl")}
    if fixture_files != set(expected_conformance):
        print("FAIL: fixture manifest does not exactly inventory validation/fixtures/*.ttl")
        return 1

    failures: list[str] = []
    for filename in sorted(expected_conformance):
        path = FIXTURES / filename
        data = parse_graph(path)
        conforms, results_graph, _results_text = validate(
            data_graph=data,
            shacl_graph=shapes,
            ont_graph=ontology,
            inference="rdfs",
            meta_shacl=True,
            advanced=True,
            abort_on_first=False,
            allow_infos=False,
            allow_warnings=False,
        )
        actual = contracted_results(results_graph)
        expected_result = expected[filename]
        if bool(conforms) != expected_conformance[filename]:
            failures.append(
                f"{filename} conformity was {bool(conforms)}, expected {expected_conformance[filename]}"
            )
        if actual != expected_result:
            missing = sorted(expected_result - actual)
            unexpected = sorted(actual - expected_result)
            if missing:
                failures.append(f"{filename} missing results: {missing}")
            if unexpected:
                failures.append(f"{filename} unexpected results: {unexpected}")
        status = "conforms" if conforms else f"fails with {len(actual)} contracted results"
        print(f"CHECK: {relative(path)} {status}")

    if failures:
        print("FAIL: SHACL proof fixtures")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "PASS: SHACL meta-validation and proof fixtures "
        f"({len(expected_conformance)} fixtures; {sum(map(len, expected.values()))} exact negative results)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
