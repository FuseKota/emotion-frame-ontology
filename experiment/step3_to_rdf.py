#!/usr/bin/env python3
"""
Step 3: Convert Plutchik scores to RDF (Turtle).

Produces FrameOccurrence + Evidence triples in the same format as
``data/sample.ttl`` so that ``scripts/run_inference.py --data`` can
consume the result directly.

Usage:
    python -m experiment.step3_to_rdf [--score-threshold 0.01]
"""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

from experiment.config import DATA_DIR, NS_EX, NS_FSCHEMA, NS_PL, PLUTCHIK_EMOTIONS

INPUT_FILE = DATA_DIR / "plutchik_scores.jsonl"
OUTPUT_FILE = DATA_DIR / "experiment_data.ttl"

PL = Namespace(NS_PL)
EX = Namespace(NS_EX)
FSCHEMA = Namespace(NS_FSCHEMA)


def main(score_threshold: float = 0.01) -> Path:
    """Build RDF graph from Plutchik scores and serialise to Turtle.

    Returns the path to the written TTL file.
    """
    print(f"Step 3: Converting to RDF (score_threshold={score_threshold})")

    g = Graph()
    g.bind("pl", PL)
    g.bind("ex", EX)
    g.bind("fschema", FSCHEMA)
    g.bind("xsd", XSD)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)

    th = Decimal(str(score_threshold))
    count = 0
    evidence_count = 0

    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            sample_id = record["id"]
            text = record["text"]
            plutchik_scores = record["plutchik_scores"]

            # Create FrameOccurrence
            fo_uri = EX[f"go_{sample_id}"]
            g.add((fo_uri, RDF.type, FSCHEMA.FrameOccurrence))
            g.add((fo_uri, RDFS.label, Literal(text[:200], datatype=XSD.string)))

            # Create Evidence nodes for each emotion above threshold
            ev_uris = []
            for emo in PLUTCHIK_EMOTIONS:
                score = Decimal(str(plutchik_scores.get(emo, 0.0)))
                if score < th:
                    continue

                ev_uri = EX[f"go_{sample_id}_ev_{emo.lower()}"]
                g.add((ev_uri, RDF.type, PL.Evidence))
                g.add((ev_uri, PL.emotion, PL[emo]))
                g.add((ev_uri, PL.score, Literal(score, datatype=XSD.decimal)))
                ev_uris.append(ev_uri)
                evidence_count += 1

            # Link evidence to FrameOccurrence
            for ev_uri in ev_uris:
                g.add((fo_uri, PL.hasEvidence, ev_uri))

            count += 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(OUTPUT_FILE), format="turtle")

    print(f"  {count} FrameOccurrences, {evidence_count} Evidence nodes")
    print(f"  Total triples: {len(g)}")
    print(f"  Written to: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Plutchik scores to RDF")
    parser.add_argument("--score-threshold", type=float, default=0.01,
                        help="Minimum score to include as Evidence (default: 0.01)")
    args = parser.parse_args()
    main(score_threshold=args.score_threshold)
