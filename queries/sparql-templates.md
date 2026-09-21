# SPARQL Templates

These templates are intended for local graph stores that load
`ontology/gdpo-1.0.0.ttl` and any relevant ABox data. The governed, executable
20-question registry and exact result oracle are
`competency-question-registry.json` and `expected-results.json`.

## Principle Target Expressions

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX gdpo: <https://www.ramsprinciplesofgooddesign.com/>

SELECT DISTINCT ?principleClass ?principleLabel ?targetExpression WHERE {
  ?principleClass rdfs:subClassOf gdpo:GDPO0000003 .
  FILTER(?principleClass != gdpo:GDPO0000003)

  ?principleClass rdfs:subClassOf ?restriction .
  ?restriction owl:onProperty gdpo:GDPO0000454 ;
               owl:allValuesFrom ?targetExpression .

  OPTIONAL { ?principleClass rdfs:label ?principleLabel . }
}
ORDER BY ?principleLabel
```

## Prescribed Process Types

```sparql
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX gdpo: <https://www.ramsprinciplesofgooddesign.com/>
PREFIX cco:  <https://www.commoncoreontologies.org/>

SELECT DISTINCT ?principleClass ?principleLabel ?processType ?processLabel WHERE {
  ?principleClass rdfs:subClassOf gdpo:GDPO0000003 .
  FILTER(?principleClass != gdpo:GDPO0000003)

  ?principleClass rdfs:subClassOf ?restriction .
  ?restriction owl:onProperty gdpo:GDPO0000062 ;
               owl:someValuesFrom ?pcExpr .

  ?pcExpr owl:intersectionOf/rdf:rest*/rdf:first ?prescribesPart .
  ?prescribesPart owl:onProperty cco:ont00001942 ;
                  owl:allValuesFrom ?processType .

  OPTIONAL { ?principleClass rdfs:label ?principleLabel . }
  OPTIONAL { ?processType rdfs:label ?processLabel . }
}
ORDER BY ?principleLabel ?processLabel
```

The `some` restriction traversed here concerns the existence of an actual
prescription-component information content entity. The nested `prescribes`
and lifecycle restrictions are universal; they do not imply that a prescribed
process or stage occurrence exists.

## Evaluation Criteria for an Artifact

```sparql
PREFIX gdpo: <https://www.ramsprinciplesofgooddesign.com/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?evaluation ?principle ?principleLabel WHERE {
  ?artifact rdfs:label "Example radio"@en .
  ?evaluation gdpo:GDPO0000045 ?artifact ;
              gdpo:GDPO0000046 ?principle .
  OPTIONAL { ?principle rdfs:label ?principleLabel . }
}
```

## Method-Derived Relevant Principles

```sparql
PREFIX gdpo: <https://www.ramsprinciplesofgooddesign.com/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?evaluation ?method ?principle ?principleLabel WHERE {
  ?evaluation gdpo:GDPO0000048 ?method .
  ?method gdpo:GDPO0000054 ?principle .
  OPTIONAL { ?principle rdfs:label ?principleLabel . }
}
ORDER BY ?evaluation ?principleLabel
```

## Score Components

```sparql
PREFIX gdpo: <https://www.ramsprinciplesofgooddesign.com/>

SELECT ?evaluation ?scoreComponent ?principle ?scoreValue ?scale WHERE {
  ?evaluation gdpo:GDPO0000457 ?scoreComponent .
  OPTIONAL { ?scoreComponent gdpo:GDPO0000458 ?principle . }
  OPTIONAL { ?scoreComponent gdpo:GDPO0000459 ?scoreValue . }
  OPTIONAL { ?scoreComponent gdpo:GDPO0000460 ?scale . }
}
```

## Communicative Honesty Evaluations

```sparql
PREFIX gdpo: <https://www.ramsprinciplesofgooddesign.com/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?evaluation ?artifact ?assessment ?criterion ?content WHERE {
  ?evaluation a gdpo:GDPO0000044 ;
              gdpo:GDPO0000045 ?artifact ;
              gdpo:GDPO0000469 ?assessment .
  ?assessment gdpo:GDPO0000470 ?criterion ;
              gdpo:GDPO0000471 ?content .
  ?criterion a gdpo:GDPO0000025 .
  ?content a ?contentType .
  ?contentType rdfs:subClassOf* gdpo:GDPO0000446 .
}
```

This template follows one assessment component, so a record-level honesty
criterion and a record-level communication-content link do not create a
spurious cross-product in a composite audit.

## Material-Bearer Provenance

```sparql
PREFIX gdpo: <https://www.ramsprinciplesofgooddesign.com/>

SELECT ?informationContent ?bearer WHERE {
  ?informationContent gdpo:GDPO0000464 ?bearer .
}
```
