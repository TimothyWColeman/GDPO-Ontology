# Contributing to GDPO

Open an issue before a material semantic change so that its scope, identifier
impact, source basis, and validation strategy can be reviewed together.

## Contribution requirements

- Do not recycle a GDPO identifier or silently change its meaning.
- Give each new class or property an English label, a definition, and suitable
  source or explanatory support.
- Explain BFO/CCO placement and every proposed restriction, equivalence,
  disjointness, inverse, or property-chain axiom.
- Update competency queries and expected results when a change affects the
  query surface.
- Add positive and negative SHACL fixtures when a change affects record
  conformance.
- Record material public changes in `CHANGELOG.md` and issue a new version IRI
  for changed published ontology bytes or semantics.
- Use synthetic examples. Do not submit confidential records, personal data,
  credentials, secrets, or material that cannot be redistributed.

## Local verification

```bash
python3 -m pip install -r requirements.txt
python3 validation/validate_suite.py
python3 scripts/build_release.py --check
```

See [`docs/validation.md`](docs/validation.md) for the individual checks.

## Pull requests

A pull request should identify the intended outcome, affected identifiers and
compatibility impact, modeling rationale, changed queries or fixtures, and the
checks run. Contributions are submitted under the repository’s
[CC BY 4.0 license](LICENSE) unless a file-specific notice states otherwise.
