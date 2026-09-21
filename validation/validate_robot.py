#!/usr/bin/env python3
"""Run ROBOT OWL 2 DL profile validation and import-closed HermiT reasoning."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef, XSD

from common import CATALOG, LOCAL_BASE, ONTOLOGY, ONTOLOGY_IRI, ROOT, parse_graph, sha256


ROBOT_SHA256 = "16a73c074f3df359a7338a84b4e0788785fe06117f931bb9796e9619ea776105"
DEFAULT_ROBOT_JAR = ROOT / "tools" / "robot" / "robot.jar"
GDPO = Namespace(LOCAL_BASE)
CCO = Namespace("https://www.commoncoreontologies.org/")
UNREAL_AWARE_CLASSES = (
    GDPO.GDPO0000003,
    GDPO.GDPO0000035,
    GDPO.GDPO0000052,
    GDPO.GDPO0000061,
)
PRESCRIPTION_COMPONENTS = tuple(GDPO[f"GDPO00000{index}"] for index in range(76, 87))
INFORMATION_CONTENT_ENTITY = CCO.ont00000958
DIRECTIVE_INFORMATION_CONTENT_ENTITY = CCO.ont00000965
PRESCRIBES = CCO.ont00001942
ABLATION_PROCESS_CLASS = GDPO.GDPO0000055


def require_robot() -> bool:
    return os.environ.get("GDPO_REQUIRE_ROBOT", "").lower() in {"1", "true", "yes"}


def java_runtime() -> str | None:
    candidates = []
    if java_home := os.environ.get("JAVA_HOME"):
        candidates.append(Path(java_home) / "bin" / "java")
    candidates.extend(
        (
            Path("/usr/local/opt/openjdk/bin/java"),
            Path("/opt/homebrew/opt/openjdk/bin/java"),
        )
    )
    if resolved := shutil.which("java"):
        candidates.append(Path(resolved))
    return next((str(path) for path in candidates if path.is_file()), None)


def robot_prefix() -> tuple[list[str] | None, str | None]:
    configured = Path(os.environ.get("ROBOT_JAR", DEFAULT_ROBOT_JAR))
    if configured.is_file():
        actual = sha256(configured)
        if actual != ROBOT_SHA256:
            return None, f"ROBOT JAR checksum mismatch: {actual} != {ROBOT_SHA256}"
        java = java_runtime()
        if not java:
            return None, "ROBOT JAR is present but no Java runtime is available"
        return [java, "-jar", str(configured)], None
    if executable := shutil.which("robot"):
        return [executable], None
    return None, "ROBOT 1.9.10 is unavailable"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def add_max_zero(graph: Graph, subject: URIRef, property_iri: URIRef) -> None:
    restriction = BNode()
    graph.add((subject, RDF.type, restriction))
    graph.add((restriction, RDF.type, OWL.Restriction))
    graph.add((restriction, OWL.onProperty, property_iri))
    graph.add(
        (
            restriction,
            OWL.maxCardinality,
            Literal(0, datatype=XSD.nonNegativeInteger),
        )
    )


def add_all_values_from(
    graph: Graph, subject: URIRef, property_iri: URIRef, filler: URIRef
) -> None:
    restriction = BNode()
    graph.add((subject, RDF.type, restriction))
    graph.add((restriction, RDF.type, OWL.Restriction))
    graph.add((restriction, OWL.onProperty, property_iri))
    graph.add((restriction, OWL.allValuesFrom, filler))


def new_probe_graph(ontology_iri: str) -> Graph:
    graph = Graph()
    probe_ontology = URIRef(ontology_iri)
    graph.add((probe_ontology, RDF.type, OWL.Ontology))
    graph.add((probe_ontology, OWL.imports, ONTOLOGY_IRI))
    return graph


def write_unreal_sentinel(path: Path) -> None:
    """Build a consistency probe that forbids fabricated process/stage fillers."""
    graph = Graph()
    sentinel_ontology = URIRef("urn:gdpo:validation:about-the-unreal-sentinel")
    graph.add((sentinel_ontology, RDF.type, OWL.Ontology))
    graph.add((sentinel_ontology, OWL.imports, ONTOLOGY_IRI))

    for index, content_class in enumerate(UNREAL_AWARE_CLASSES, start=1):
        individual = URIRef(f"urn:gdpo:validation:unreal-aware-content-{index}")
        graph.add((individual, RDF.type, content_class))
        add_max_zero(graph, individual, CCO.ont00001942)

    for component in PRESCRIPTION_COMPONENTS:
        add_max_zero(graph, component, CCO.ont00001942)
        add_max_zero(graph, component, GDPO.GDPO0000063)

    graph.serialize(path, format="turtle")


def write_directive_ablation(path: Path, case: str) -> tuple[URIRef, URIRef | None]:
    """Build one import-closed directive-typing consequence probe."""
    graph = new_probe_graph(f"urn:gdpo:validation:directive-ablation:{case}")
    content = URIRef(f"urn:gdpo:validation:{case}-content")
    graph.add((content, RDF.type, OWL.NamedIndividual))
    add_all_values_from(graph, content, PRESCRIBES, ABLATION_PROCESS_CLASS)

    process = None
    if case == "prospective":
        graph.add((content, RDF.type, INFORMATION_CONTENT_ENTITY))
        add_max_zero(graph, content, PRESCRIBES)
    elif case == "formal-directive":
        graph.add((content, RDF.type, DIRECTIVE_INFORMATION_CONTENT_ENTITY))
        add_max_zero(graph, content, PRESCRIBES)
    elif case == "application-grounded":
        graph.add((content, RDF.type, INFORMATION_CONTENT_ENTITY))
        process = URIRef("urn:gdpo:validation:documented-evaluation-process")
        graph.add((process, RDF.type, OWL.NamedIndividual))
        graph.add((process, RDF.type, ABLATION_PROCESS_CLASS))
        graph.add((content, PRESCRIBES, process))
    else:
        raise ValueError(f"unknown directive ablation case: {case}")

    graph.serialize(path, format="turtle")
    return content, process


def write_disjoint_universal_probe(path: Path, case: str) -> None:
    """Build a probe with two universal restrictions and disjoint fillers."""
    graph = new_probe_graph(f"urn:gdpo:validation:disjoint-universal:{case}")
    content = URIRef(f"urn:gdpo:validation:{case}-universal-content")
    allowed_process_class_a = URIRef("urn:gdpo:validation:allowed-process-class-a")
    allowed_process_class_b = URIRef("urn:gdpo:validation:allowed-process-class-b")
    graph.add((content, RDF.type, OWL.NamedIndividual))
    graph.add((content, RDF.type, INFORMATION_CONTENT_ENTITY))
    for allowed_class in (allowed_process_class_a, allowed_process_class_b):
        graph.add((allowed_class, RDF.type, OWL.Class))
        graph.add((allowed_class, RDFS.subClassOf, ABLATION_PROCESS_CLASS))
        add_all_values_from(graph, content, PRESCRIBES, allowed_class)
    graph.add((allowed_process_class_a, OWL.disjointWith, allowed_process_class_b))

    if case == "zero-filler":
        add_max_zero(graph, content, PRESCRIBES)
    elif case == "asserted-filler":
        filler = URIRef("urn:gdpo:validation:asserted-evaluation-process")
        graph.add((filler, RDF.type, OWL.NamedIndividual))
        graph.add((content, PRESCRIBES, filler))
    else:
        raise ValueError(f"unknown disjoint universal case: {case}")

    graph.serialize(path, format="turtle")


def hermit_reason(
    prefix: list[str],
    input_path: Path,
    output_path: Path,
    *,
    class_assertions: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        *prefix,
        "reason",
        "--catalog",
        str(CATALOG),
        "--input",
        str(input_path),
        "--reasoner",
        "HermiT",
    ]
    if class_assertions:
        command.extend(
            ["--axiom-generators", "ClassAssertion", "--include-indirect", "true"]
        )
    command.extend(["--output", str(output_path)])
    return run(command)


def main() -> int:
    prefix, unavailable = robot_prefix()
    if prefix is None:
        if require_robot():
            print(f"FAIL: {unavailable}; CI requires ROBOT/HermiT")
            return 1
        print(f"SKIP: {unavailable}; set ROBOT_JAR or install robot to run DL gates")
        return 0

    common = ["--catalog", str(CATALOG), "--input", str(ONTOLOGY)]
    profile = run([*prefix, "validate-profile", "--profile", "DL", *common])
    if profile.returncode:
        print("FAIL: ROBOT OWL 2 DL profile validation")
        print(profile.stdout.rstrip())
        return profile.returncode
    print("PASS: ROBOT OWL 2 DL profile validation")

    with tempfile.TemporaryDirectory(prefix="gdpo-robot-") as temp_dir:
        reasoned = Path(temp_dir) / "gdpo-reasoned.owl"
        reason = run(
            [
                *prefix,
                "reason",
                *common,
                "--reasoner",
                "HermiT",
                "--output",
                str(reasoned),
            ]
        )
        if reason.returncode:
            print("FAIL: import-closed HermiT consistency/classification")
            print(reason.stdout.rstrip())
            return reason.returncode
        graph = parse_graph(reasoned)
        unsatisfiable = {
            subject
            for subject in graph.subjects(RDFS.subClassOf, OWL.Nothing)
            if isinstance(subject, URIRef) and str(subject).startswith(LOCAL_BASE)
        }
        if unsatisfiable:
            print(
                "FAIL: HermiT classified local named classes as unsatisfiable: "
                + ", ".join(sorted(map(str, unsatisfiable)))
            )
            return 1
        sentinel = Path(temp_dir) / "about-the-unreal-sentinel.ttl"
        sentinel_reasoned = Path(temp_dir) / "about-the-unreal-sentinel-reasoned.owl"
        write_unreal_sentinel(sentinel)
        sentinel_reason = hermit_reason(prefix, sentinel, sentinel_reasoned)
        if sentinel_reason.returncode:
            print(
                "FAIL: import-closed About the Unreal sentinel; a normative "
                "content class still entails a prescribed process or lifecycle stage"
            )
            print(sentinel_reason.stdout.rstrip())
            return sentinel_reason.returncode

        prospective = Path(temp_dir) / "directive-ablation-prospective.ttl"
        prospective_reasoned = Path(temp_dir) / "directive-ablation-prospective.owl"
        write_directive_ablation(prospective, "prospective")
        prospective_reason = hermit_reason(prefix, prospective, prospective_reasoned)
        if prospective_reason.returncode:
            print(
                "FAIL: generic ICE + prescribes only Process + max 0 prescribes "
                "must remain satisfiable"
            )
            print(prospective_reason.stdout.rstrip())
            return prospective_reason.returncode

        formal_directive = Path(temp_dir) / "directive-ablation-formal-directive.ttl"
        formal_directive_reasoned = (
            Path(temp_dir) / "directive-ablation-formal-directive.owl"
        )
        write_directive_ablation(formal_directive, "formal-directive")
        formal_directive_reason = hermit_reason(
            prefix, formal_directive, formal_directive_reasoned
        )
        if formal_directive_reason.returncode == 0:
            print(
                "FAIL: formal CCO Directive ICE + prescribes only Process + max 0 "
                "prescribes was unexpectedly satisfiable"
            )
            return 1
        if "inconsistent" not in formal_directive_reason.stdout.casefold():
            print(
                "FAIL: formal Directive ICE negative probe failed for a reason other "
                "than the expected ontology inconsistency"
            )
            print(formal_directive_reason.stdout.rstrip())
            return formal_directive_reason.returncode

        application = Path(temp_dir) / "directive-ablation-application-grounded.ttl"
        application_reasoned = (
            Path(temp_dir) / "directive-ablation-application-grounded.owl"
        )
        application_content, _ = write_directive_ablation(
            application, "application-grounded"
        )
        application_reason = hermit_reason(
            prefix, application, application_reasoned, class_assertions=True
        )
        if application_reason.returncode:
            print(
                "FAIL: application-grounded prescribes assertion could not be "
                "classified by import-closed HermiT"
            )
            print(application_reason.stdout.rstrip())
            return application_reason.returncode
        application_graph = parse_graph(application_reasoned)
        if (
            application_content,
            RDF.type,
            DIRECTIVE_INFORMATION_CONTENT_ENTITY,
        ) not in application_graph:
            print(
                "FAIL: genuine prescribes assertion did not infer CCO Directive "
                "Information Content Entity"
            )
            return 1

        zero_filler = Path(temp_dir) / "disjoint-universal-zero-filler.ttl"
        zero_filler_reasoned = Path(temp_dir) / "disjoint-universal-zero-filler.owl"
        write_disjoint_universal_probe(zero_filler, "zero-filler")
        zero_filler_reason = hermit_reason(
            prefix, zero_filler, zero_filler_reasoned
        )
        if zero_filler_reason.returncode:
            print(
                "FAIL: universal restriction with a disjoint alternative must "
                "remain satisfiable when prescribes has zero fillers"
            )
            print(zero_filler_reason.stdout.rstrip())
            return zero_filler_reason.returncode

        asserted_filler = Path(temp_dir) / "disjoint-universal-asserted-filler.ttl"
        asserted_filler_reasoned = (
            Path(temp_dir) / "disjoint-universal-asserted-filler.owl"
        )
        write_disjoint_universal_probe(asserted_filler, "asserted-filler")
        asserted_filler_reason = hermit_reason(
            prefix, asserted_filler, asserted_filler_reasoned
        )
        if asserted_filler_reason.returncode == 0:
            print(
                "FAIL: one asserted prescribes filler constrained by two disjoint "
                "universal filler classes was unexpectedly consistent"
            )
            return 1
        if "inconsistent" not in asserted_filler_reason.stdout.casefold():
            print(
                "FAIL: asserted-filler universal probe failed for a reason "
                "other than the expected ontology inconsistency"
            )
            print(asserted_filler_reason.stdout.rstrip())
            return asserted_filler_reason.returncode
    print(
        "PASS: import-closed HermiT consistency/classification "
        "(0 unsatisfiable local named classes)"
    )
    print(
        "PASS: import-closed About the Unreal sentinel "
        "(zero prescribed-process/lifecycle fillers remain consistent)"
    )
    print(
        "PASS: import-closed Directive ICE ablation "
        "(prospective ICE is satisfiable with zero fillers; formal Directive ICE "
        "is inconsistent with zero fillers; an asserted prescribes relation "
        "infers Directive ICE)"
    )
    print(
        "PASS: import-closed conditional-universal countermodel "
        "(two disjoint universal fillers remain satisfiable at zero values; one "
        "asserted value activates both constraints and is inconsistent)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
