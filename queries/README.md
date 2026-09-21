# Competency queries

`competency-question-registry.json` maps the twenty competency questions to
their executable evidence. `expected-results.json` is the exact result
contract. The `example/` directory contains seven reusable example queries.

Run the complete contract with:

```bash
python3 validation/validate_queries.py
```

Update the expected result file only after a reviewed semantic change:

```bash
python3 validation/validate_queries.py --update-contract
```
