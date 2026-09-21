# SHACL shapes

`gdpo-shapes.ttl` defines a practical closed-world profile for supplied design
evaluation records and score components. The shapes complement the ontology’s
open-world semantics; they do not replace OWL reasoning or expert review.

Run the positive and negative fixture checks with:

```bash
python3 validation/validate_shacl.py
```

The competency-query registry and assessment fixture supply additional
retrieval and inference checks.
