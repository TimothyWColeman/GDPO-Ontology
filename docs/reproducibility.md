# Reproducibility

The repository contains executable material supporting the ontology’s modeled
patterns. It is organized as ordinary public repository documentation.

## Included evidence

- [`examples/assessment-fixture.ttl`](../examples/assessment-fixture.ttl) is a
  synthetic ABox with artifact evaluations, method specifications, scores, and
  a communicative-honesty assessment component.
- [`queries/example/`](../queries/example/) contains seven example queries.
- [`queries/`](../queries/) contains the full twenty-question competency-query
  registry and exact result contract.
- [`shapes/gdpo-shapes.ttl`](../shapes/gdpo-shapes.ttl) contains SHACL shapes
  for evaluation-record conformance.
- [`validation/`](../validation/) contains executable checks.

## Run the public checks

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 validation/validate_assessment_fixture.py
python3 validation/validate_queries.py
python3 validation/validate_shacl.py
```

The assessment-fixture check verifies target-expression and query behavior,
method-derived relevance, and the paired communicative-honesty consequence
under OWL-RL materialization. The full suite adds release identity, dependency,
OWL profile, and deterministic-build checks.
