<p align="center">
  <img src="docs/img/gdpo-readme-banner.svg" alt="Good Design Principles Ontology: normative guidance, process prescriptions, and evaluation traceability" width="100%">
</p>

# Good Design Principles Ontology (GDPO)

**Public baseline: v1.0.0, 21 September 2026**

GDPO is an applied ontology for representing Dieter Rams’ ten principles of
good design as normative information content, artifact-associated targets,
process guidance, and traceable design evaluations. It aligns with BFO 2020
and the Common Core Ontologies (CCO).

The ontology does not decide whether an artifact is good design. It provides a
semantic structure for documenting principles, methods, criteria, assessed
artifacts, evaluation processes, temporal context, and scores.

## Release identity

| Item | Value |
|---|---|
| Public release | `v1.0.0` |
| Stable ontology IRI | `https://www.ramsprinciplesofgooddesign.com/GoodDesignPrinciplesOntology` |
| Version IRI | `https://www.ramsprinciplesofgooddesign.com/GoodDesignPrinciplesOntology20260921v1.0.0` |
| Canonical serialization | [`ontology/gdpo-1.0.0.ttl`](ontology/gdpo-1.0.0.ttl) |
| License | [CC BY 4.0](LICENSE) |

## Contents

- [`ontology/`](ontology/) contains the OWL ontology and local XML catalog.
- [`imports/`](imports/) contains checksum-verified BFO and CCO dependency
  snapshots and their notices.
- [`examples/`](examples/) contains synthetic ABox data for inspection and
  regression testing.
- [`queries/`](queries/) contains twenty competency questions and exact result
  contracts.
- [`shapes/`](shapes/) contains SHACL conformance shapes.
- [`validation/`](validation/) contains executable structural, SHACL, query,
  and OWL-DL checks.
- [`docs/`](docs/) explains the model, competency questions, imports,
  reproducibility, validation, and governance.

## Quick start

Open [`ontology/gdpo-1.0.0.ttl`](ontology/gdpo-1.0.0.ttl) in Protégé or another
OWL tool. The committed [`ontology/catalog-v001.xml`](ontology/catalog-v001.xml)
maps GDPO and its dependencies to the local files.

To run the executable checks:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 validation/validate_suite.py
```

The ROBOT/HermiT check is optional when its runtime is unavailable locally and
is required by the repository workflow. See [`docs/validation.md`](docs/validation.md).

## Core modeling ideas

GDPO keeps the following distinct:

- a principle category and the named information-content statement that bears
  its canonical formulation;
- a principle and the quality, function, disposition, process, or information
  content it concerns;
- a method specification, the evaluation process that applies it, and the
  evaluation record produced by that process; and
- a composite evaluation record and the individual criterion–subject
  assessment components it contains.

The last distinction is important for composite audits. A communicative-honesty
evaluation is classified only when one assessment component pairs an honesty
criterion with design communication content. Independent record-level links do
not establish that pairing.

See [`docs/modeling-patterns.md`](docs/modeling-patterns.md) for the full
pattern descriptions.

## Reproducibility and citation

The repository supplies the examples, queries, shapes, and validation tools
needed to inspect the modeled claims. Instructions are in
[`docs/reproducibility.md`](docs/reproducibility.md).

Please cite GDPO 1.0 using [`CITATION.cff`](CITATION.cff) and identify the
release version used. See [`NOTICE`](NOTICE) for source attribution and
third-party notices.
