"""Shared release constants and helpers for GDPO validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from rdflib import Graph, URIRef


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
VERSION = VERSION_FILE.read_text(encoding="utf-8").strip()
RELEASE_DATE = "2026-09-21"
ONTOLOGY = ROOT / "ontology" / f"gdpo-{VERSION}.ttl"
CATALOG = ROOT / "ontology" / "catalog-v001.xml"
IMPORT_LOCK = ROOT / "imports" / "import-lock.json"
ONTOLOGY_IRI = URIRef(
    "https://www.ramsprinciplesofgooddesign.com/GoodDesignPrinciplesOntology"
)
VERSION_IRI = URIRef(
    "https://www.ramsprinciplesofgooddesign.com/"
    f"GoodDesignPrinciplesOntology20260921v{VERSION}"
)
LOCAL_BASE = "https://www.ramsprinciplesofgooddesign.com/"


def parse_graph(path: Path) -> Graph:
    graph = Graph()
    graph.parse(path)
    return graph


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()
