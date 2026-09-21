# Competency questions

The machine-readable registry is
[`queries/competency-question-registry.json`](../queries/competency-question-registry.json).
Each question below has an executable query or a documented structural check.
The exact expected results are recorded in
[`queries/expected-results.json`](../queries/expected-results.json).

| ID | Question | Evidence |
|---|---|---|
| CQ-01 | Which target class expressions are associated with each principle? | `queries/example/a2-1-target-expressions.rq` |
| CQ-02 | Which process types constrain the intended prescriptions of each principle? | `queries/cq02-prescribed-process-types.rq` |
| CQ-03 | Which lifecycle-stage process types constrain each prescription's intended applicability? | `queries/cq03-lifecycle-applicability.rq` |
| CQ-04 | Which principles are included in the Rams ten principles specification? | `queries/cq04-specification-components.rq` |
| CQ-05 | How does GDPO distinguish principles from artifact-side qualities, functions, and dispositions? | Structural check and `queries/cq05-principle-target-distinction.rq` |
| CQ-06 | What artifacts have been evaluated? | `queries/cq06-evaluated-artifacts.rq` |
| CQ-07 | Which principle criterion was an artifact evaluated against? | `queries/cq07-evaluation-criteria.rq` |
| CQ-08 | During which temporal region was the evaluation assessed? | `queries/cq08-evaluation-temporal-regions.rq` |
| CQ-09 | Which method specification was used? | `queries/cq09-evaluation-methods.rq` |
| CQ-10 | What score values and scales are associated with the evaluation? | `queries/cq10-evaluation-scores.rq` |
| CQ-11 | Which methods operationalize which principles? | `queries/example/a2-6-method-operationalizations.rq` |
| CQ-12 | Which principles are relevant because of method use? | `queries/cq12-method-derived-relevance.rq` |
| CQ-13 | Which principles were explicitly selected as criteria? | `queries/cq13-explicit-criteria.rq` |
| CQ-14 | Which records are honesty evaluations? | `queries/cq14-honesty-evaluations.rq` |
| CQ-15 | Which records include a paired honesty–communication assessment? | `queries/example/a2-4-communicative-honesty.rq` |
| CQ-16 | Which communication content entities occur as assessed subjects? | `queries/cq16-assessed-communication-content.rq` |
| CQ-17 | How are material and functional honesty distinguished? | Structural check and `queries/cq17-honesty-facets.rq` |
| CQ-18 | Which evaluation process produced a record? | `queries/cq18-producing-processes.rq` |
| CQ-19 | Which agent carried out an evaluation process? | `queries/cq19-evaluation-agents.rq` |
| CQ-20 | Which information content entities have material-bearer provenance? | `queries/cq20-material-bearers.rq` |

Run all twenty contracts with:

```bash
python3 validation/validate_queries.py
```
