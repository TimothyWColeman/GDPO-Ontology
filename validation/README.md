# Validation tooling

Run the full suite from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 validation/validate_suite.py
```

The suite validates release metadata, local dependencies, OWL structure, SHACL
fixtures, competency-query results, assessment-fixture consequences, optional
ROBOT/HermiT reasoning, and deterministic release packaging.

Individual entry points are:

- `validate_version.py` for v1.0.0 metadata and public-baseline identity.
- `validate_imports.py` for the local dependency closure and digests.
- `validate_gdpo.py` for structural invariants.
- `validate_shacl.py` for positive and negative SHACL fixtures.
- `validate_queries.py` for all twenty competency questions.
- `validate_assessment_fixture.py` for example-query and OWL-RL checks.
- `validate_robot.py` for OWL 2 DL profile and HermiT checks.

ROBOT/HermiT is skipped if unavailable unless `GDPO_REQUIRE_ROBOT=1` is set.
