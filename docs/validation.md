# Validation

Run the integrated suite from the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 validation/validate_suite.py
```

The suite checks:

- release metadata and version identity;
- local import closure and dependency digests;
- OWL structure and modeling invariants;
- positive and negative SHACL fixtures;
- twenty competency-question result contracts;
- OWL-RL consequences for the assessment fixture;
- OWL 2 DL profile and HermiT reasoning when ROBOT is available; and
- deterministic release packaging.

To require ROBOT/HermiT locally, provide a compatible ROBOT installation and
set `GDPO_REQUIRE_ROBOT=1`. The GitHub workflow installs ROBOT and requires that
gate before publishing release assets.

To check packaging determinism without creating a release archive in `dist/`:

```bash
python3 scripts/build_release.py --check
```
