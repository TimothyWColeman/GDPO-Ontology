#!/usr/bin/env python3
"""Execute all 20 GDPO competency questions against exact result contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from rdflib import BNode, Graph
from rdflib.compare import to_canonical_graph

from common import ONTOLOGY, ROOT, VERSION, parse_graph, relative


FIXTURE = ROOT / "examples" / "assessment-fixture.ttl"
REGISTRY = ROOT / "queries" / "competency-question-registry.json"
CONTRACT = ROOT / "queries" / "expected-results.json"
CQ_DOC = ROOT / "docs" / "competency-questions.md"
EXPECTED_IDS = [f"CQ-{index:02d}" for index in range(1, 21)]


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def serialized_rows(result, *, permit_bnodes: bool) -> tuple[list[str], list[list[str | None]]]:
    variables = [str(variable) for variable in result.vars]
    rows = []
    for row in result:
        values = row.asdict()
        serialized = []
        for variable in variables:
            term = values.get(variable)
            if isinstance(term, BNode) and not permit_bnodes:
                raise ValueError(
                    "OWL-RL contracts may not expose unstable blank-node identifiers"
                )
            serialized.append(None if term is None else term.n3())
        rows.append(serialized)
    rows.sort(key=lambda row: json.dumps(row, ensure_ascii=False))
    return variables, rows


def documented_questions() -> list[tuple[str, str]]:
    questions: list[tuple[str, str]] = []
    for line in CQ_DOC.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if (
            len(cells) < 2
            or cells[0] == "ID"
            or set(cells[0]) <= {"-", ":"}
            or not re.fullmatch(r"CQ-[0-9]{2}", cells[0])
        ):
            continue
        questions.append((cells[0], re.sub(r"`([^`]+)`", r"\1", cells[1])))
    return questions


def load_registry() -> tuple[dict, list[dict]]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if registry.get("schema_version") != "1.0":
        raise ValueError("registry schema_version must be 1.0")
    if registry.get("gdpo_version") != VERSION:
        raise ValueError("registry gdpo_version does not match VERSION")
    entries = registry.get("competency_questions")
    if not isinstance(entries, list) or [entry.get("id") for entry in entries] != EXPECTED_IDS:
        raise ValueError("registry must contain ordered, unique CQ-01 through CQ-20")
    questions = [(entry.get("id"), entry.get("question")) for entry in entries]
    if questions != documented_questions():
        raise ValueError(
            "docs/competency-questions.md CQ IDs/text/order differ from the registry"
        )
    root_queries = {relative(path) for path in (ROOT / "queries").glob("*.rq")}
    registered_root_queries = {
        entry["query"]
        for entry in entries
        if Path(entry["query"]).parent.as_posix() == "queries"
    }
    if root_queries != registered_root_queries:
        raise ValueError("root query files are not exactly inventoried by the CQ registry")
    for entry in entries:
        if entry.get("inference") not in {"asserted", "owlrl"}:
            raise ValueError(f"{entry['id']} has an unsupported inference mode")
        if entry.get("execution_kind") == "schema-structural-review" and not entry.get(
            "review_note"
        ):
            raise ValueError(f"{entry['id']} lacks its required review_note")
        query_path = ROOT / entry["query"]
        if not query_path.is_file():
            raise ValueError(f"{entry['id']} query is missing: {entry['query']}")
    return registry, entries


def evaluate() -> dict:
    registry, entries = load_registry()
    combined = Graph()
    combined += parse_graph(ONTOLOGY)
    combined += parse_graph(FIXTURE)
    asserted_graph = to_canonical_graph(combined)
    inferred_graph: Graph | None = None
    contracts = {}

    for entry in entries:
        query_path = ROOT / entry["query"]
        query_text = query_path.read_text(encoding="utf-8")
        if entry["inference"] == "owlrl":
            if inferred_graph is None:
                inferred_graph = Graph()
                inferred_graph += combined
                DeductiveClosure(OWLRL_Semantics).expand(inferred_graph)
            graph = inferred_graph
            permit_bnodes = False
        else:
            graph = asserted_graph
            permit_bnodes = True
        result = graph.query(query_text)
        variables, rows = serialized_rows(result, permit_bnodes=permit_bnodes)
        contracts[entry["id"]] = {
            "question": entry["question"],
            "execution_kind": entry["execution_kind"],
            "inference": entry["inference"],
            "query": entry["query"],
            "query_sha256": digest_text(query_text),
            "variables": variables,
            "row_count": len(rows),
            "rows": rows,
        }

    return {
        "schema_version": "2.0",
        "gdpo_version": VERSION,
        "registry": relative(REGISTRY),
        "registry_sha256": digest_text(REGISTRY.read_text(encoding="utf-8")),
        "dataset": [relative(ONTOLOGY), relative(FIXTURE)],
        "contracts": contracts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--update-contract",
        action="store_true",
        help="replace the exact oracle after an intentional, reviewed semantic change",
    )
    args = parser.parse_args()
    try:
        actual = evaluate()
    except Exception as exc:
        print(f"FAIL: competency-question registry or evaluation: {exc}")
        return 1

    if args.update_contract:
        CONTRACT.write_text(
            json.dumps(actual, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"UPDATED: {relative(CONTRACT)}")
        return 0
    if not CONTRACT.is_file():
        print(f"FAIL: exact result contract is missing: {relative(CONTRACT)}")
        return 1
    try:
        expected = json.loads(CONTRACT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"FAIL: exact result contract is invalid JSON: {exc}")
        return 1
    if actual != expected:
        print("FAIL: competency-question results differ from the governed exact contract")
        actual_contracts = actual.get("contracts", {})
        expected_contracts = expected.get("contracts", {})
        for cq_id in EXPECTED_IDS:
            if actual_contracts.get(cq_id) != expected_contracts.get(cq_id):
                expected_rows = expected_contracts.get(cq_id, {}).get("row_count")
                actual_rows = actual_contracts.get(cq_id, {}).get("row_count")
                print(f"- {cq_id}: expected {expected_rows} rows, found {actual_rows}")
        print("  Use --update-contract only after reviewing the semantic diff.")
        return 1
    total_rows = sum(item["row_count"] for item in actual["contracts"].values())
    kinds: dict[str, int] = {}
    for cq_id in EXPECTED_IDS:
        contract = actual["contracts"][cq_id]
        kinds[contract["execution_kind"]] = kinds.get(contract["execution_kind"], 0) + 1
        print(
            f"CHECK: {cq_id} [{contract['execution_kind']}; {contract['inference']}] "
            f"= {contract['row_count']} exact rows"
        )
    print(
        "PASS: complete competency-question registry "
        f"(20/20 questions; {total_rows} total exact rows; modes {kinds})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
