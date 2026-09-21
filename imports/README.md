# Local dependency snapshots

This directory contains the BFO 2020 and CCO modules required by the canonical
GDPO ontology. They are committed as local, checksum-verified snapshots so the
catalog and validation suite can resolve imports reproducibly without relying
on a live network service.

`import-lock.json` records each file’s upstream source URL, ontology IRI,
version IRI, local path, and SHA-256 digest. Run
`python3 validation/validate_imports.py` to verify the closure.

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for upstream license and
notice information.
