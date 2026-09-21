# Modeling patterns

## Principle and target expression

A design-principle category is distinct from the artifact-associated entity it
concerns. GDPO uses OWL class expressions to represent the intended target of a
principle. A target can involve a quality, function, disposition, material
basis, process, communication content, or measurement-information class.

The ten canonical formulations are represented as named information-content
individuals with source attribution. They are not used as substitutes for the
classes that categorize design principles.

## Process guidance and lifecycle applicability

Named prescription components constrain the class of a compatible prescribed
process or lifecycle-stage process. These universal restrictions do not assert
that a process occurrence exists. Applications that record actual prescriptions
or conformance can add the relevant individuals and relations.

## Evaluation traceability

GDPO separates an evaluation method specification from the evaluation process
that applies it and from the evaluation record produced by that process. A
record can identify an evaluated artifact, explicit criterion, method,
assessment temporal region, agent, and score components.

Method-derived relevance is distinct from an explicitly selected criterion. A
method can operationalize one or more principles, while an evaluation record
can state the principle or principles used as its actual criteria.

## Criterion–subject assessment components

A composite evaluation may involve multiple criteria and multiple assessed
subjects. Independent record-level links cannot show which subject was assessed
under which criterion. GDPO therefore uses a criterion–subject assessment
component that holds exactly one selected principle and one assessed subject.

The communicative-honesty pattern requires one component whose criterion is a
principle of honesty and whose subject is design communication content. This
allows the ontology to classify a qualified record without treating unrelated
record-level links as a paired assessment.

## Contextualized scores and environmental profiles

A score component carries a value, a scored principle, and a scale
specification. It does not make an evaluation result an intrinsic property of
an artifact.

The environmental-performance profile is measurement information. A domain
profile that needs detailed lifecycle comparisons should state the product
system, lifecycle boundary and stages, method, functional unit, baseline, and
assessment time.
