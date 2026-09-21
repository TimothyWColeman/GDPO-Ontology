#!/usr/bin/env python3
"""Structural, annotation, modeling-pattern, and OWL-RL regression checks."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import BNode, Graph, Namespace, OWL, RDF, RDFS, SKOS, URIRef, XSD
from rdflib.collection import Collection

from common import LOCAL_BASE, ONTOLOGY, ROOT, parse_graph, relative


EXAMPLE = ROOT / "examples" / "gdpo-example-abox.ttl"
POSITIVE_FIXTURE = ROOT / "validation" / "fixtures" / "positive-evaluation.ttl"
GDPO = Namespace(LOCAL_BASE)
CCO = Namespace("https://www.commoncoreontologies.org/")
EXAMPLE_NS = Namespace("https://example.org/gdpo-example/")
VALIDATION_NS = Namespace("https://example.org/gdpo-validation/")
LOCAL_ID = re.compile(r"GDPO[0-9]{7}$")
SCHEMA_TYPES = {
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    OWL.AnnotationProperty,
}
PRINCIPLE_STATEMENTS = {GDPO[f"GDPO00000{i}"] for i in range(66, 76)}
PRESCRIPTION_COMPONENTS = {GDPO[f"GDPO00000{i}"] for i in range(76, 87)}
UNREAL_AWARE_CONTENT_CLASSES = {
    GDPO.GDPO0000003,
    GDPO.GDPO0000035,
    GDPO.GDPO0000052,
    GDPO.GDPO0000061,
}
COMMUNICATIVE_HONESTY_RECORD = EXAMPLE_NS[
    "example-radio-communicative-honesty-evaluation-record"
]
COMMUNICATIVE_HONESTY_COMPONENT = EXAMPLE_NS[
    "example-radio-label-honesty-assessment"
]
PAIRED_COMPONENT = VALIDATION_NS["paired-honesty-assessment"]
CROSSED_RECORD = VALIDATION_NS["crossed-criterion-subject-record"]
CROSSED_HONESTY_COMPONENT = VALIDATION_NS["crossed-honesty-artifact-assessment"]
CROSSED_COMMUNICATION_COMPONENT = VALIDATION_NS[
    "crossed-durability-communication-assessment"
]


def restriction_fillers(
    graph: Graph, subject: URIRef, property_iri: URIRef, quantifier: URIRef
) -> list:
    fillers = []
    for expression in graph.objects(subject, RDF.type):
        if not isinstance(expression, BNode):
            continue
        if (expression, RDF.type, OWL.Restriction) not in graph:
            continue
        if (expression, OWL.onProperty, property_iri) not in graph:
            continue
        fillers.extend(graph.objects(expression, quantifier))
    return fillers


def union_members(graph: Graph, expression) -> set:
    if isinstance(expression, URIRef):
        return {expression}
    if not isinstance(expression, BNode):
        return set()
    heads = list(graph.objects(expression, OWL.unionOf))
    if len(heads) != 1:
        return set()
    return set(Collection(graph, heads[0]))


def equivalent_intersection_members(graph: Graph, subject: URIRef) -> list:
    """Return the one named class's equivalent intersection, if it has one."""

    expressions = list(graph.objects(subject, OWL.equivalentClass))
    if len(expressions) != 1 or not isinstance(expressions[0], BNode):
        return []
    heads = list(graph.objects(expressions[0], OWL.intersectionOf))
    if len(heads) != 1:
        return []
    return list(Collection(graph, heads[0]))


def has_some_restriction(
    graph: Graph, members: list, property_iri: URIRef, filler: URIRef
) -> bool:
    return any(
        isinstance(member, BNode)
        and (member, RDF.type, OWL.Restriction) in graph
        and (member, OWL.onProperty, property_iri) in graph
        and (member, OWL.someValuesFrom, filler) in graph
        for member in members
    )


def has_exact_qualified_restriction(
    graph: Graph, members: list, property_iri: URIRef, filler: URIRef
) -> bool:
    return any(
        isinstance(member, BNode)
        and (member, RDF.type, OWL.Restriction) in graph
        and (member, OWL.onProperty, property_iri) in graph
        and (member, OWL.onClass, filler) in graph
        and any(
            str(cardinality) == "1"
            and cardinality.datatype == XSD.nonNegativeInteger
            for cardinality in graph.objects(member, OWL.qualifiedCardinality)
        )
        for member in members
    )


def check_schema_annotations(graph: Graph, failures: list[str]) -> tuple[int, int, int]:
    local_schema = {
        subject
        for subject, _, entity_type in graph.triples((None, RDF.type, None))
        if entity_type in SCHEMA_TYPES
        and isinstance(subject, URIRef)
        and str(subject).startswith(LOCAL_BASE)
    }
    class_count = sum((term, RDF.type, OWL.Class) in graph for term in local_schema)
    object_count = sum(
        (term, RDF.type, OWL.ObjectProperty) in graph for term in local_schema
    )
    datatype_count = sum(
        (term, RDF.type, OWL.DatatypeProperty) in graph for term in local_schema
    )
    for term in sorted(local_schema):
        local_name = str(term).removeprefix(LOCAL_BASE)
        if not LOCAL_ID.fullmatch(local_name):
            failures.append(f"invalid local schema identifier: {term}")
        if not list(graph.objects(term, RDFS.label)):
            failures.append(f"local schema entity lacks rdfs:label: {term}")
        if not list(graph.objects(term, SKOS.definition)):
            failures.append(f"local schema entity lacks skos:definition: {term}")
    return class_count, object_count, datatype_count


def check_no_punning_or_has_value(graph: Graph, failures: list[str]) -> None:
    has_values = list(graph.triples((None, OWL.hasValue, None)))
    if has_values:
        failures.append(f"found {len(has_values)} owl:hasValue triple(s)")
    classes = {
        subject
        for subject in graph.subjects(RDF.type, OWL.Class)
        if isinstance(subject, URIRef) and str(subject).startswith(LOCAL_BASE)
    }
    individuals = {
        subject
        for subject in graph.subjects(RDF.type, OWL.NamedIndividual)
        if isinstance(subject, URIRef) and str(subject).startswith(LOCAL_BASE)
    }
    overlap = classes & individuals
    if overlap:
        failures.append(
            "GDPO class/individual punning found: "
            + ", ".join(sorted(map(str, overlap)))
        )


def check_criterion_subject_assessment_contract(
    graph: Graph, failures: list[str]
) -> None:
    """Guard the reified pair used by communicative-honesty classification."""

    assessment_component = GDPO.GDPO0000469
    assessment_criterion = GDPO.GDPO0000470
    assessed_subject = GDPO.GDPO0000471
    assessment_class = GDPO.GDPO0000472
    communicative_component = GDPO.GDPO0000473
    evaluation_record = GDPO.GDPO0000044
    design_principle = GDPO.GDPO0000003
    honesty_principle = GDPO.GDPO0000025
    communication_content = GDPO.GDPO0000446
    bfo_entity = URIRef("http://purl.obolibrary.org/obo/BFO_0000001")
    communicative_evaluation = GDPO.GDPO0000452
    honesty_evaluation = GDPO.GDPO0000455

    expected_properties = {
        assessment_component: (evaluation_record, assessment_class, None),
        assessment_criterion: (assessment_class, design_principle, CCO.ont00001808),
        assessed_subject: (assessment_class, bfo_entity, CCO.ont00001808),
    }
    for property_iri, (domain, range_, superproperty) in expected_properties.items():
        if set(graph.objects(property_iri, RDFS.domain)) != {domain}:
            failures.append(
                f"criterion–subject property has unexpected domain: {property_iri}"
            )
        if set(graph.objects(property_iri, RDFS.range)) != {range_}:
            failures.append(
                f"criterion–subject property has unexpected range: {property_iri}"
            )
        if superproperty is not None and (
            property_iri,
            RDFS.subPropertyOf,
            superproperty,
        ) not in graph:
            failures.append(
                f"criterion–subject property lacks CCO is-about specialization: {property_iri}"
            )
        if list(graph.objects(property_iri, OWL.propertyChainAxiom)):
            failures.append(
                f"criterion–subject pairing must not use a property chain: {property_iri}"
            )

    assessment_members = equivalent_intersection_members(graph, assessment_class)
    if (
        CCO.ont00000958 not in assessment_members
        or not has_exact_qualified_restriction(
            graph, assessment_members, assessment_criterion, design_principle
        )
        or not has_exact_qualified_restriction(
            graph, assessment_members, assessed_subject, bfo_entity
        )
    ):
        failures.append(
            "criterion–subject assessment component must be an ICE with exactly one "
            "design-principle criterion and exactly one BFO entity subject"
        )

    communicative_members = equivalent_intersection_members(graph, communicative_component)
    if (
        assessment_class not in communicative_members
        or not has_some_restriction(
            graph, communicative_members, assessment_criterion, honesty_principle
        )
        or not has_some_restriction(
            graph, communicative_members, assessed_subject, communication_content
        )
    ):
        failures.append(
            "communicative-honesty assessment component must pair honesty with "
            "design communication content"
        )

    communicative_members = equivalent_intersection_members(graph, communicative_evaluation)
    if (
        honesty_evaluation not in communicative_members
        or not has_some_restriction(
            graph,
            communicative_members,
            assessment_component,
            communicative_component,
        )
        or any(
            isinstance(member, BNode)
            and (member, OWL.onProperty, GDPO.GDPO0000450) in graph
            for member in communicative_members
        )
    ):
        failures.append(
            "design communicative honesty evaluation must require a paired "
            "communicative-honesty assessment component, not independent "
            "record-level communication content"
        )

    honesty_members = equivalent_intersection_members(graph, honesty_evaluation)
    if (
        evaluation_record not in honesty_members
        or not has_some_restriction(
            graph, honesty_members, GDPO.GDPO0000046, honesty_principle
        )
    ):
        failures.append(
            "design honesty evaluation must retain its record-level honesty criterion"
        )


def check_prescription_components(graph: Graph, failures: list[str]) -> None:
    directive_subclasses = {
        subject
        for subject in graph.subjects(RDFS.subClassOf, CCO.ont00000965)
        if isinstance(subject, URIRef) and str(subject).startswith(LOCAL_BASE)
    }
    if directive_subclasses:
        failures.append(
            "unreal-aware local content class inherits CCO Directive ICE's "
            "existential commitment: "
            + ", ".join(sorted(map(str, directive_subclasses)))
        )
    for content_class in sorted(UNREAL_AWARE_CONTENT_CLASSES):
        if (content_class, RDFS.subClassOf, CCO.ont00000958) not in graph:
            failures.append(
                "unreal-aware content class must directly specialize CCO Information "
                f"Content Entity: {content_class}"
            )
    target_domains = set(graph.objects(GDPO.GDPO0000454, RDFS.domain))
    if target_domains != {GDPO.GDPO0000003}:
        failures.append(
            "aims at artifact-side target must have exactly design principle as its "
            f"domain; found {sorted(map(str, target_domains))}"
        )

    for property_iri, label in (
        (CCO.ont00001942, "prescribed process"),
        (GDPO.GDPO0000063, "lifecycle-stage"),
    ):
        global_existentials = {
            expression
            for expression in graph.subjects(OWL.onProperty, property_iri)
            if (expression, RDF.type, OWL.Restriction) in graph
            and list(graph.objects(expression, OWL.someValuesFrom))
        }
        if global_existentials:
            failures.append(
                f"authored graph contains unintended {label} existential restrictions: "
                + ", ".join(sorted(map(str, global_existentials)))
            )

    actual_components = {
        subject
        for subject in graph.subjects(RDF.type, GDPO.GDPO0000061)
        if isinstance(subject, URIRef) and str(subject).startswith(LOCAL_BASE)
    }
    if actual_components != PRESCRIPTION_COMPONENTS:
        failures.append(
            "named prescription component inventory mismatch: expected 11; found "
            + ", ".join(sorted(map(str, actual_components)))
        )

    linked = set()
    link_counts: Counter = Counter()
    for statement in PRINCIPLE_STATEMENTS:
        components = set(graph.objects(statement, GDPO.GDPO0000062))
        linked.update(components)
        link_counts.update(components)
        if not components:
            failures.append(f"principle statement has no prescription component: {statement}")
    if linked != PRESCRIPTION_COMPONENTS:
        failures.append("principle statements do not link exactly the 11 governed components")
    multiply_linked = [component for component, count in link_counts.items() if count != 1]
    if multiply_linked:
        failures.append(
            "prescription components must each belong to exactly one statement: "
            + ", ".join(sorted(map(str, multiply_linked)))
        )

    lifecycle_components = 0
    for component in sorted(PRESCRIPTION_COMPONENTS):
        if (component, RDF.type, OWL.NamedIndividual) not in graph:
            failures.append(f"component is not an owl:NamedIndividual: {component}")
        for predicate in (CCO.ont00001942, GDPO.GDPO0000063, GDPO.GDPO0000467):
            direct_values = list(graph.objects(component, predicate))
            if direct_values:
                failures.append(
                    f"component uses class-level intent as direct ABox values via {predicate}: "
                    f"{component}"
                )

        process_some = restriction_fillers(
            graph, component, CCO.ont00001942, OWL.someValuesFrom
        )
        process_only = restriction_fillers(
            graph, component, CCO.ont00001942, OWL.allValuesFrom
        )
        if process_some:
            failures.append(
                "component must not existentially imply a prescribed process "
                f"occurrence: {component}"
            )
        if len(process_only) != 1 or not union_members(graph, process_only[0]):
            failures.append(
                f"component must have exactly one universal process restriction: {component}"
            )

        stage_some = restriction_fillers(
            graph, component, GDPO.GDPO0000063, OWL.someValuesFrom
        )
        stage_only = restriction_fillers(
            graph, component, GDPO.GDPO0000063, OWL.allValuesFrom
        )
        if stage_some:
            failures.append(
                "component must not existentially imply a lifecycle-stage "
                f"occurrence: {component}"
            )
        if stage_some or stage_only:
            lifecycle_components += 1
            if len(stage_only) != 1 or not union_members(graph, stage_only[0]):
                failures.append(
                    f"lifecycle-qualified component lacks one universal stage restriction: {component}"
                )
    if lifecycle_components != 7:
        failures.append(
            f"expected 7 lifecycle-qualified named components, found {lifecycle_components}"
        )


def check_honesty_realization_contract(graph: Graph, failures: list[str]) -> None:
    """Keep the parent, named facet, and expanded honesty target synchronized."""

    realization = URIRef("http://purl.obolibrary.org/obo/BFO_0000054")
    interaction = GDPO.GDPO0000017
    manufacturing = GDPO.GDPO0000037
    use_maintenance = GDPO.GDPO0000039
    expected_material = {interaction, use_maintenance}

    def subclass_fillers(subject: URIRef, property_iri: URIRef) -> list:
        fillers = []
        for expression in graph.objects(subject, RDFS.subClassOf):
            if not isinstance(expression, BNode):
                continue
            if (expression, RDF.type, OWL.Restriction) not in graph:
                continue
            if (expression, OWL.onProperty, property_iri) not in graph:
                continue
            fillers.extend(graph.objects(expression, OWL.allValuesFrom))
        return fillers

    def nested_subclass_fillers(subject: URIRef, property_iri: URIRef) -> list:
        pending = list(graph.objects(subject, RDFS.subClassOf))
        seen = set()
        fillers = []
        while pending:
            expression = pending.pop()
            if expression in seen:
                continue
            seen.add(expression)
            if isinstance(expression, BNode):
                if (expression, OWL.onProperty, property_iri) in graph:
                    fillers.extend(graph.objects(expression, OWL.allValuesFrom))
                for predicate in (OWL.intersectionOf, OWL.unionOf):
                    for head in graph.objects(expression, predicate):
                        pending.extend(Collection(graph, head))
        return fillers

    parent_fillers = nested_subclass_fillers(GDPO.GDPO0000009, realization)
    parent_members = (
        union_members(graph, parent_fillers[0]) if len(parent_fillers) == 1 else set()
    )
    if parent_members != expected_material:
        failures.append(
            "design honesty realization union must be exactly interaction and "
            f"use/maintenance; found {sorted(map(str, parent_members))}"
        )

    material_fillers = subclass_fillers(GDPO.GDPO0000041, realization)
    material_members = (
        union_members(graph, material_fillers[0]) if len(material_fillers) == 1 else set()
    )
    if material_members != expected_material:
        failures.append(
            "named material-honesty realization union must be exactly interaction and "
            f"use/maintenance; found {sorted(map(str, material_members))}"
        )

    principle_targets = subclass_fillers(GDPO.GDPO0000025, GDPO.GDPO0000454)
    expanded_material_members: set = set()
    if len(principle_targets) == 1:
        for branch in union_members(graph, principle_targets[0]):
            if not isinstance(branch, BNode):
                continue
            intersections = list(graph.objects(branch, OWL.intersectionOf))
            if len(intersections) != 1:
                continue
            terms = set(Collection(graph, intersections[0]))
            if GDPO.GDPO0000041 not in terms:
                continue
            for term in terms:
                if not isinstance(term, BNode):
                    continue
                if (term, OWL.onProperty, realization) not in graph:
                    continue
                fillers = list(graph.objects(term, OWL.allValuesFrom))
                if len(fillers) == 1:
                    expanded_material_members = union_members(graph, fillers[0])
    if expanded_material_members != expected_material:
        failures.append(
            "expanded honesty material branch must match the named material-honesty "
            "realization union; found "
            + ", ".join(sorted(map(str, expanded_material_members)))
        )
    if manufacturing in parent_members | material_members | expanded_material_members:
        failures.append(
            "manufacturing must configure the honesty bearer/material basis, not be a "
            "permitted honesty-realization process"
        )


def check_example_inference(
    ontology_graph: Graph, example_graph: Graph, failures: list[str]
) -> None:
    generic_record = GDPO.GDPO0000044
    advertisement_content = GDPO.GDPO0000449
    honesty_evaluation = GDPO.GDPO0000455
    communicative_honesty_evaluation = GDPO.GDPO0000452
    wrong_type = (COMMUNICATIVE_HONESTY_RECORD, RDF.type, advertisement_content)
    if wrong_type in example_graph:
        failures.append(
            "communicative-honesty evaluation record is typed as advertisement content"
        )
    if (COMMUNICATIVE_HONESTY_RECORD, RDF.type, generic_record) not in example_graph:
        failures.append("communicative-honesty example lacks generic record type")
    if (
        COMMUNICATIVE_HONESTY_RECORD,
        RDF.type,
        communicative_honesty_evaluation,
    ) in example_graph:
        failures.append("communicative-honesty specialization must be inferred, not asserted")

    combined = ontology_graph + example_graph
    DeductiveClosure(OWLRL_Semantics).expand(combined)
    expected_types = {
        generic_record,
        honesty_evaluation,
        communicative_honesty_evaluation,
    }
    missing = {
        class_iri
        for class_iri in expected_types
        if (COMMUNICATIVE_HONESTY_RECORD, RDF.type, class_iri) not in combined
    }
    if missing:
        failures.append(
            "communicative-honesty inference missing types: "
            + ", ".join(sorted(map(str, missing)))
        )
    if (
        COMMUNICATIVE_HONESTY_COMPONENT,
        RDF.type,
        GDPO.GDPO0000473,
    ) not in combined:
        failures.append(
            "communicative-honesty example lacks an inferred paired assessment component"
        )


def check_crossed_pair_non_inference(
    ontology_graph: Graph, fixture_graph: Graph, failures: list[str]
) -> None:
    """Ensure record-level co-occurrence cannot substitute for a paired component."""

    honesty_evaluation = GDPO.GDPO0000455
    communicative_honesty_evaluation = GDPO.GDPO0000452
    communicative_component = GDPO.GDPO0000473
    if (
        CROSSED_RECORD,
        GDPO.GDPO0000046,
        GDPO.GDPO0000071,
    ) not in fixture_graph or (
        CROSSED_RECORD,
        GDPO.GDPO0000450,
        VALIDATION_NS["communication-content"],
    ) not in fixture_graph:
        failures.append("crossed criterion–subject control lacks record-level co-occurrence")
        return

    combined = ontology_graph + fixture_graph
    DeductiveClosure(OWLRL_Semantics).expand(combined)
    if (PAIRED_COMPONENT, RDF.type, communicative_component) not in combined:
        failures.append(
            "positive criterion–subject component was not inferred as communicative honesty"
        )
    if (CROSSED_RECORD, RDF.type, honesty_evaluation) not in combined:
        failures.append("crossed criterion–subject control lost broad honesty classification")
    if (CROSSED_RECORD, RDF.type, communicative_honesty_evaluation) in combined:
        failures.append(
            "crossed criterion–subject control was incorrectly inferred as a "
            "communicative-honesty evaluation"
        )
    for component in (CROSSED_HONESTY_COMPONENT, CROSSED_COMMUNICATION_COMPONENT):
        if (component, RDF.type, communicative_component) in combined:
            failures.append(
                "crossed criterion–subject component was incorrectly inferred as "
                f"communicative honesty: {component}"
            )


def main() -> int:
    failures: list[str] = []
    try:
        ontology_graph = parse_graph(ONTOLOGY)
        example_graph = parse_graph(EXAMPLE)
        positive_fixture_graph = parse_graph(POSITIVE_FIXTURE)
    except Exception as exc:
        print(f"FAIL: RDF parsing: {exc}", file=sys.stderr)
        return 1

    class_count, object_count, datatype_count = check_schema_annotations(
        ontology_graph, failures
    )
    check_no_punning_or_has_value(ontology_graph, failures)
    check_prescription_components(ontology_graph, failures)
    check_honesty_realization_contract(ontology_graph, failures)
    check_criterion_subject_assessment_contract(ontology_graph, failures)
    check_example_inference(ontology_graph, example_graph, failures)
    check_crossed_pair_non_inference(ontology_graph, positive_fixture_graph, failures)

    if failures:
        print("FAIL: GDPO structural and semantic regressions")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "PASS: GDPO structural and semantic regressions "
        f"({len(ontology_graph)} triples; {class_count} local classes; "
        f"{object_count} object properties; {datatype_count} datatype properties; "
        "11 universally constrained named prescription components; "
        "no process/lifecycle existentials; paired OWL-RL entailments present)"
    )
    print(f"PASS: parsed {relative(EXAMPLE)}")
    print(f"PASS: parsed {relative(POSITIVE_FIXTURE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
