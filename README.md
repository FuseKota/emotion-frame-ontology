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

## Plutchik Dyad Module

An extension module that implements Plutchik's wheel of emotions theory for compound emotion (dyad) inference.

### Overview

The Plutchik Dyad module (`modules/EFO-PlutchikDyad.ttl`) defines:
- **8 Basic Emotions**: Joy, Trust, Fear, Surprise, Sadness, Disgust, Anger, Anticipation
- **10 Dyads** (compound emotions): Love, Submission, Awe, Disapproval, Remorse, Contempt, Aggressiveness, Optimism, Hope, Pride

### Dyad Definitions

| Dyad | Components | Type |
|------|------------|------|
| Love | Joy + Trust | Primary |
| Submission | Trust + Fear | Primary |
| Awe | Fear + Surprise | Primary |
| Disapproval | Surprise + Sadness | Primary |
| Remorse | Sadness + Disgust | Primary |
| Contempt | Disgust + Anger | Primary |
| Aggressiveness | Anger + Anticipation | Primary |
| Optimism | Anticipation + Joy | Primary |
| Hope | Anticipation + Trust | Secondary |
| Pride | Anger + Joy | Secondary |

### Running Dyad Inference

```bash
# Install dependencies
pip install -r requirements.txt

# Run inference with default threshold (0.4)
python scripts/run_inference.py --out output/out.ttl

# Run with custom threshold
python scripts/run_inference.py --th 0.5 --out output/out.ttl
```

### Inference Algorithm

1. For each `FrameOccurrence`, collect all `EmotionEvidence` nodes
2. For each dyad, check if both component emotions have evidence above threshold
3. If yes, compute `dyadScore = min(score1, score2)`
4. Materialize:
   - `FrameOccurrence pl:satisfiesEmotion Dyad`
   - New `EmotionEvidence` with score, derivedFrom, and inferenceMethod

### Expected Results (sample.ttl)

| Situation | Evidence | Expected Dyad | Score |
|-----------|----------|---------------|-------|
| ex:s1 | Joy=0.80, Trust=0.70 | Love | 0.70 |
| ex:s2 | Disgust=0.60, Anger=0.60 | Contempt | 0.60 |
| ex:s3 | Anger=0.90, Anticipation=0.50 | Aggressiveness | 0.50 |
| ex:s4 | Surprise=0.60, Sadness=0.45 | Disapproval | 0.45 |
| ex:s5 | Anticipation=0.42, Trust=0.41 | Hope | 0.41 |
| ex:s6 | Fear=0.39, Surprise=0.80 | (none) | - |

Note: ex:s6 has Fear below threshold (0.39 < 0.4), so Awe is not inferred.

### Viewing Results in Protege

1. Open Protege
2. Load all files:
   - `data/EmoCore_iswc.ttl`
   - `modules/EFO-PlutchikDyad.ttl`
   - `data/sample.ttl`
   - `output/out.ttl`
3. Navigate to Individuals to see inferred `EmotionEvidence` nodes with `pl:satisfiesEmotion` relations

### Module Namespaces

| Prefix | IRI |
|--------|-----|
| `pl:` | `http://example.org/efo/plutchik#` |
| `emo:` | `http://www.ontologydesignpatterns.org/ont/emotions/EmoCore.owl#` |
| `ex:` | `http://example.org/data#` |

## Directory Structure

```
efo_repro/
├── README.md
├── WORK_LOG.md                   # Reproduction work log (Japanese)
├── requirements.txt              # Python dependencies
├── data/
│   ├── EmoCore_iswc.ttl          # Core emotion vocabulary
│   ├── BE_iswc.ttl               # Basic Emotions module (EFO-BE)
│   ├── BasicEmotionTriggers_iswc.ttl  # Trigger patterns
│   └── sample.ttl                # Sample data for dyad inference
├── docs/
│   ├── architecture.md           # System architecture
│   ├── inference-pipeline.md     # Inference pipeline details
│   ├── validation-and-cq.md      # SHACL validation & CQ queries
│   └── design-decisions.md       # Design decisions & rationale
├── imports/
│   ├── DUL.owl                   # DOLCE-Ultralite
│   └── catalog-v001.xml          # Protege IRI resolution
├── modules/
│   └── EFO-PlutchikDyad.ttl      # Plutchik Dyad extension module
├── output/
│   ├── out.ttl                   # Inference output (generated)
│   └── threshold_sensitivity.csv # Threshold sweep results (generated)
├── shacl/
│   └── plutchik-dyad-shapes.ttl  # SHACL shape definitions
├── sparql/
│   ├── 01_list_be_emotions.rq
│   ├── 02_intensity_relations.rq
│   ├── 03_optional_relations.rq
│   ├── 04_impediments.rq
│   ├── 05_ontology_stats.rq
│   ├── cq/                       # Competency question queries (7)
│   └── dyad_rules/               # SPARQL CONSTRUCT rules (10)
└── scripts/
    ├── download.sh               # Download all ontologies
    ├── extract_imports.py        # Analyze owl:imports
    ├── run_fuseki.sh             # Fuseki management
    ├── run_inference.py          # Plutchik dyad inference
    ├── threshold_sweep.py        # Threshold sensitivity analysis
    └── validate_shacl.py         # SHACL validation
```

## Documentation

Detailed documentation is available in the `docs/` directory:

| Document | Description |
|----------|-------------|
| [Paper Summary](docs/paper-summary.md) | Summary of the EFO paper (De Giorgis & Gangemi, 2024): architecture, modules, evaluation, and multimodal extensions |
| [Architecture](docs/architecture.md) | System architecture: ontology module structure, namespaces, class hierarchy, properties, and data flow |
| [Inference Pipeline](docs/inference-pipeline.md) | Min-threshold algorithm, SPARQL CONSTRUCT rules, test data design, and threshold sensitivity analysis |
| [Validation and CQ](docs/validation-and-cq.md) | SHACL shape definitions, validation script usage, competency question queries, and quality checks |
| [Design Decisions](docs/design-decisions.md) | Design rationale: paper correspondence, key design choices, and known limitations |

## References

- Paper: https://arxiv.org/abs/2401.10751
- GitHub: https://github.com/StenDoipanni/EFO
- Atlas of Emotions: http://atlasofemotions.org
- DOLCE-Ultralite: http://www.ontologydesignpatterns.org/ont/dul/DUL.owl
- Plutchik's Wheel of Emotions: https://en.wikipedia.org/wiki/Robert_Plutchik
