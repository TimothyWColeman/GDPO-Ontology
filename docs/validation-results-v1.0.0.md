# Validation results — v1.0.0

This summary records the public baseline's validation surface. Re-run
[`validation/validate_suite.py`](../validation/validate_suite.py) to verify the
current checkout; the executable files and exact contracts are authoritative.

| Check | Public v1.0.0 result |
|---|---|
| Release identity | Version `1.0.0`, public version IRI, and 21 September 2026 issue date agree across release files. |
| Import closure | Seven checksum-verified BFO/CCO artifacts; 18 catalog mappings; 128 referenced external entities owned locally. |
| Ontology structure | 1,635 RDF triples; 58 local classes; 25 object properties; three datatype properties; 11 universally constrained named prescription components; no process or lifecycle existential restrictions. |
| SHACL | Positive fixture conforms; negative fixture yields exactly 17 contracted results. |
| Competency questions | All 20 contracts pass with 101 exact RDF-term rows across asserted, inferred, and schema-level scopes. |
| Assessment fixture | Seven example-query/inference checks pass, including method-derived relevance and the paired communicative-honesty consequence. |
| OWL 2 DL and HermiT | The GitHub release workflow installs ROBOT 1.9.10 and requires this gate. A local run reports an explicit skip when ROBOT is unavailable. |
| Release packaging | The deterministic public archive check passes. |

These checks establish the stated structural, retrieval, and bounded
application-data claims. They do not certify a concrete artifact as good
design or replace domain evidence and expert judgment.
