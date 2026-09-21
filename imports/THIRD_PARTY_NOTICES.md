# Third-Party Import Notices

The files listed in `import-lock.json` are unmodified third-party ontology
snapshots. They are bundled to make GDPO validation reproducible and retain
their upstream terms. No GDPO license supersedes or expands those grants.

## Basic Formal Ontology 2020

- Bundled file: `bfo-core.owl`
- Release: `release-2024-01-29`
- Upstream: <https://github.com/BFO-ontology/BFO-2020/tree/release-2024-01-29>
- License declared by the bundled ontology: Creative Commons Attribution 4.0
  International, <https://creativecommons.org/licenses/by/4.0/>

Creator and contributor attribution is retained in the ontology artifact and
its upstream project history.

## Common Core Ontologies 2.0

- Bundled files: `cco-*.ttl`
- Release: `v2.0-2024-11-06`
- Upstream:
  <https://github.com/CommonCoreOntology/CommonCoreOntologies/releases/tag/v2.0-2024-11-06>
- License declared by each bundled module: BSD 3-Clause

```text
BSD 3-Clause License

Copyright (c) 2017, CUBRC, INC

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Integrity

`import-lock.json` records the exact upstream source URL, ontology IRI, version
IRI, local path, and SHA-256 digest for every bundled artifact. Verify those
records with:

```bash
python3 validation/validate_imports.py
```
