#!/usr/bin/env python3
"""Check the public assessment fixture's queries and OWL-RL consequences."""

from __future__ import annotations

import sys
from pathlib import Path

import owlrl
import rdflib
from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import Graph, Namespace, OWL, RDF

from common import ONTOLOGY, ROOT


FIXTURE = ROOT / "examples" / "assessment-fixture.ttl"
QUERY_DIR = ROOT / "queries" / "example"
GDPO = Namespace("https://www.ramsprinciplesofgooddesign.com/")
EXAMPLE = Namespace("http://example.org/gdpo-demo/")

QUERY_FILES = {
    "target expressions": "a2-1-target-expressions.rq",
    "artifact evaluations": "a2-2-artifact-evaluations.rq",
    "artifact comparison": "a2-3-artifact-comparison.rq",
    "communicative honesty": "a2-4-communicative-honesty.rq",
    "disposition realization": "a2-5-disposition-realization.rq",
    "method operationalizations": "a2-6-method-operationalizations.rq",
    "lifecycle applicability": "a2-7-lifecycle-applicability.rq",
}

EXPECTED_QUERY_ROWS = {
    "target expressions": 10,
    "artifact evaluations": 3,
    "artifact comparison": 2,
    "communicative honesty": 1,
    "disposition realization": 1,
    "method operationalizations": 3,
    "lifecycle applicability": 7,
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_turtle(path: Path) -> Graph:
    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


def combined_graph(ontology_graph: Graph, fixture_graph: Graph) -> Graph:
    graph = Graph()
    for triple in ontology_graph:
        graph.add(triple)
    for triple in fixture_graph:
        graph.add(triple)
    return graph


def query_row_counts(graph: Graph) -> dict[str, int]:
    return {
        label: len(list(graph.query((QUERY_DIR / filename).read_text(encoding="utf-8"))))
        for label, filename in QUERY_FILES.items()
    }


def gdpo_punning_overlap(graph: Graph) -> set:
    classes = {
        subject
        for subject in graph.subjects(RDF.type, OWL.Class)
        if str(subject).startswith(str(GDPO))
    }
    individuals = {
        subject
        for subject in graph.subjects(RDF.type, OWL.NamedIndividual)
        if str(subject).startswith(str(GDPO))
    }
    return classes & individuals


def main() -> None:
    ontology_graph = parse_turtle(ONTOLOGY)
    fixture_graph = parse_turtle(FIXTURE)
    graph = combined_graph(ontology_graph, fixture_graph)

    has_value_count = len(list(ontology_graph.triples((None, OWL.hasValue, None))))
    if has_value_count:
        fail(f"found {has_value_count} owl:hasValue triple(s)")
    punning_overlap = gdpo_punning_overlap(ontology_graph)
    if punning_overlap:
        fail("GDPO class/named-individual overlap: " + ", ".join(map(str, punning_overlap)))
    wrong_example_type = (
        EXAMPLE["Eval_SK4_ManualHonesty_2024"],
        RDF.type,
        GDPO["GDPO0000449"],
    )
    if wrong_example_type in fixture_graph:
        fail("manual-honesty evaluation is typed as product advertisement content")

    query_counts = query_row_counts(graph)
    for label, expected in EXPECTED_QUERY_ROWS.items():
        if query_counts[label] != expected:
            fail(f"{label} returned {query_counts[label]} row(s), expected {expected}")

    DeductiveClosure(OWLRL_Semantics).expand(graph)
    durability_evaluation = EXAMPLE["Eval_SK4_Durability_2024"]
    expected_relevance = {GDPO["GDPO0000072"], GDPO["GDPO0000074"]}
    actual_relevance = set(graph.objects(durability_evaluation, GDPO["GDPO0000059"]))
    if actual_relevance != expected_relevance:
        fail("durability relevance does not match the expected method-derived set")

    honesty_evaluation = EXAMPLE["Eval_SK4_ManualHonesty_2024"]
    required_honesty_types = {
        GDPO["GDPO0000044"],
        GDPO["GDPO0000452"],
        GDPO["GDPO0000455"],
    }
    honesty_types = set(graph.objects(honesty_evaluation, RDF.type))
    if not required_honesty_types.issubset(honesty_types):
        missing = required_honesty_types - honesty_types
        fail("manual-honesty inference is missing type(s): " + ", ".join(map(str, missing)))
    honesty_component = EXAMPLE["Assessment_SK4_ManualHonesty_2024"]
    if (honesty_component, RDF.type, GDPO["GDPO0000473"]) not in graph:
        fail("manual-honesty inference lacks the paired communicative-honesty component")

    print("GDPO assessment-fixture validation")
    print(f"RDFLib: {rdflib.__version__}")
    print(f"OWL-RL: {owlrl.__version__}")
    print(f"Ontology: {ONTOLOGY.relative_to(ROOT)}")
    print(f"Fixture: {FIXTURE.relative_to(ROOT)}")
    for label in QUERY_FILES:
        print(f"  {label}: {query_counts[label]} rows")
    print("PASS: query and OWL-RL assessment-fixture checks succeeded")


if __name__ == "__main__":
    main()
