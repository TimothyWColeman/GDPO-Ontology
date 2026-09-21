# Imports and local resolution

GDPO imports BFO 2020 and selected CCO modules. The repository includes local
snapshots of the required files so that the ontology and validation suite can
be inspected without depending on live network resolution.

`ontology/catalog-v001.xml` maps the stable GDPO IRI, the v1.0.0 version IRI,
and the dependency IRIs to the committed local files. Configure the catalog in
an OWL tool when working from a checkout.

`imports/import-lock.json` records the upstream release URL, ontology IRI,
version IRI, local path, and SHA-256 digest for each bundled dependency. Verify
the closure with:

```bash
python3 validation/validate_imports.py
```

The dependency files retain their upstream license and notice terms. See
[`imports/THIRD_PARTY_NOTICES.md`](../imports/THIRD_PARTY_NOTICES.md).
