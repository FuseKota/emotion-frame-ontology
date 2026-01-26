# EFO (Emotion Frame Ontology) Reproduction

This repository contains the reproduction setup for the EFO ontology from:

> De Giorgis, S., & Gangemi, A. (2024). **EFO: the Emotion Frame Ontology**. arXiv:2401.10751

## Overview

EFO treats emotions as semantic frames, following a Frame Semantics approach aligned with the DOLCE foundational ontology.

### Ontology Modules

| Module | File | Description |
|--------|------|-------------|
| **EmoCore** | `EmoCore_iswc.ttl` | Core vocabulary for emotions as semantic frames |
| **EFO-BE** | `BE_iswc.ttl` | Basic Emotions module (Ekman's theory) |
| **BasicEmotionTriggers** | `BasicEmotionTriggers_iswc.ttl` | Emotion trigger patterns (optional) |

### Key Classes and Properties

- `emo:Emotion` - Base emotion class
- `be:BE_Emotion` - Basic Emotion class (6 emotions: Anger, Fear, Sadness, Disgust, Enjoyment, Surprise)
- `be:moreIntenseThan` / `be:lessIntenseThan` - Intensity relations
- `be:hasAntidote` - Therapeutic interventions
- `be:hasImpediment` - Blocking factors
- `be:hasPreCondition` - Preconditions for emotions

## Setup

### 1. Download Ontologies

```bash
./scripts/download.sh
```

This downloads:
- EmoCore and EFO-BE from GitHub: https://github.com/StenDoipanni/EFO
- DUL.owl (DOLCE-Ultralite) from: http://www.ontologydesignpatterns.org/ont/dul/DUL.owl

### 2. Open in Protege

1. Open Protege
2. File > Open > Select `data/BE_iswc.ttl`
3. Protege should automatically resolve imports using `imports/catalog-v001.xml`

If imports fail to resolve:
1. File > Preferences > New Entities
2. Ensure "Auto-update imports" is enabled
3. Add the `imports/` directory to the catalog search path

### 3. Load into Apache Jena Fuseki

Prerequisites: Install [Apache Jena Fuseki](https://jena.apache.org/download/)

```bash
# Start Fuseki server
./scripts/run_fuseki.sh start

# Load ontologies
./scripts/run_fuseki.sh load

# Run validation queries
./scripts/run_fuseki.sh query

# Stop server
./scripts/run_fuseki.sh stop
```

Web UI: http://localhost:3030
SPARQL Endpoint: http://localhost:3030/efo/sparql

### 4. Alternative: Python with rdflib

```python
from rdflib import Graph

g = Graph()
g.parse("imports/DUL.owl", format="xml")
g.parse("data/EmoCore_iswc.ttl", format="turtle")
g.parse("data/BE_iswc.ttl", format="turtle")

# Query BE_Emotion subclasses
query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX be: <http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl#>

SELECT DISTINCT ?emotion WHERE {
    ?emotion rdfs:subClassOf* be:BE_Emotion .
    ?emotion a owl:Class .
}
"""
for row in g.query(query):
    print(row.emotion)
```

## SPARQL Queries

### Query 1: List BE_Emotion Classes

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX be: <http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl#>

SELECT DISTINCT ?emotion WHERE {
    ?emotion rdfs:subClassOf* be:BE_Emotion .
    ?emotion a owl:Class .
}
ORDER BY ?emotion
```

Expected output: ~140 emotion classes including Anger, Fear, Sadness, Disgust, Enjoyment, Surprise and their sub-emotions.

### Query 2: Intensity Relations

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX be: <http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl#>

SELECT DISTINCT ?strongerEmotion ?weakerEmotion WHERE {
    ?strongerEmotion rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty be:moreIntenseThan ;
        owl:someValuesFrom ?weakerEmotion
    ] .
}
ORDER BY ?strongerEmotion
```

Expected output: Intensity hierarchy (e.g., Fury > Rage > Anger > Annoyance)

### Query 3: Antidotes

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX be: <http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl#>

SELECT DISTINCT ?emotion ?antidote WHERE {
    ?emotion rdfs:subClassOf [
        a owl:Restriction ;
        owl:onProperty be:hasAntidote ;
        owl:someValuesFrom ?antidote
    ] .
}
ORDER BY ?emotion
```

## Dependencies

| IRI | Source | File |
|-----|--------|------|
| `http://www.ontologydesignpatterns.org/ont/dul/DUL.owl` | OntologyDesignPatterns.org | `imports/DUL.owl` |

### Referenced (not imported)

The following IRIs are referenced in the ontologies but not explicitly imported:
- `https://w3id.org/framester/schema/` - Framester schema classes
- `http://dbpedia.org/resource/Emotion` - DBpedia emotion concept

These do not require local copies for basic functionality.

## Directory Structure

```
efo_repro/
├── README.md
├── data/
│   ├── EmoCore_iswc.ttl          # Core emotion vocabulary
│   ├── BE_iswc.ttl               # Basic Emotions module (EFO-BE)
│   └── BasicEmotionTriggers_iswc.ttl  # Trigger patterns
├── imports/
│   ├── DUL.owl                   # DOLCE-Ultralite
│   └── catalog-v001.xml          # Protege IRI resolution
├── sparql/
│   ├── 01_list_be_emotions.rq
│   ├── 02_intensity_relations.rq
│   ├── 03_optional_relations.rq
│   ├── 04_impediments.rq
│   └── 05_ontology_stats.rq
└── scripts/
    ├── download.sh               # Download all ontologies
    ├── extract_imports.py        # Analyze owl:imports
    └── run_fuseki.sh             # Fuseki management
```

## References

- Paper: https://arxiv.org/abs/2401.10751
- GitHub: https://github.com/StenDoipanni/EFO
- Atlas of Emotions: http://atlasofemotions.org
- DOLCE-Ultralite: http://www.ontologydesignpatterns.org/ont/dul/DUL.owl
