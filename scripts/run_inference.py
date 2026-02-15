#!/usr/bin/env python3
"""
Plutchik Dyad Inference Script

Performs min-threshold aggregation to infer compound emotions (dyads)
from basic emotion evidence scores.

Usage:
    python scripts/run_inference.py [--th THRESHOLD] [--out OUTPUT_FILE]
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

# Namespaces
PL = Namespace("http://example.org/efo/plutchik#")
EMO = Namespace("http://www.ontologydesignpatterns.org/ont/emotions/EmoCore.owl#")
FSCHEMA = Namespace("https://w3id.org/framester/schema/")
EX = Namespace("http://example.org/data#")
OUTPUT_ONTOLOGY = URIRef("http://example.org/efo/plutchik/inference")

# Dyad definitions: dyad_name -> (component1, component2)
DYADS: Dict[str, Tuple[str, str]] = {
    "Love": ("Joy", "Trust"),
    "Submission": ("Trust", "Fear"),
    "Awe": ("Fear", "Surprise"),
    "Disapproval": ("Surprise", "Sadness"),
    "Remorse": ("Sadness", "Disgust"),
    "Contempt": ("Disgust", "Anger"),
    "Aggressiveness": ("Anger", "Anticipation"),
    "Optimism": ("Anticipation", "Joy"),
    "Hope": ("Anticipation", "Trust"),
    "Pride": ("Anger", "Joy"),
}


def load_graph(base_dir: Path, data_file: Optional[str] = None) -> Graph:
    """Load all required TTL files into a single graph.

    Parameters
    ----------
    base_dir : Path
        Repository root directory.
    data_file : str, optional
        Path to an alternative data file.  When *None* (default) the
        bundled ``data/sample.ttl`` is used, preserving backward
        compatibility.
    """
    g = Graph()

    # Bind namespaces
    g.bind("pl", PL)
    g.bind("emo", EMO)
    g.bind("fschema", FSCHEMA)
    g.bind("ex", EX)
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)

    # Resolve data file path
    if data_file:
        data_path = Path(data_file)
        if not data_path.is_absolute():
            data_path = base_dir / data_file
    else:
        data_path = base_dir / "data" / "sample.ttl"

    # Required files
    required_files = [
        base_dir / "data" / "EmoCore_iswc.ttl",
        base_dir / "modules" / "EFO-PlutchikDyad.ttl",
        data_path,
    ]

    for f in required_files:
        if not f.exists():
            raise FileNotFoundError(f"Required file not found: {f}")
        print(f"Loading: {f}")
        g.parse(f, format="turtle")

    # Optional files (EFO-BE, BET)
    optional_files = [
        base_dir / "data" / "BE_iswc.ttl",
        base_dir / "data" / "BasicEmotionTriggers_iswc.ttl",
    ]
    for f in optional_files:
        if f.exists():
            print(f"Loading (optional): {f}")
            g.parse(f, format="turtle")

    print(f"Total triples loaded: {len(g)}")
    return g


def get_frame_occurrences(g: Graph) -> List[URIRef]:
    """Get all FrameOccurrence instances."""
    query = """
    SELECT DISTINCT ?fo WHERE {
        ?fo a fschema:FrameOccurrence .
    }
    """
    results = g.query(query, initNs={"fschema": FSCHEMA})
    return [row.fo for row in results]


def get_evidence_for_frame(g: Graph, frame_occ: URIRef) -> Dict[str, Tuple[URIRef, Decimal]]:
    """
    Get emotion evidence for a FrameOccurrence.
    Returns dict: emotion_local_name -> (evidence_uri, score)
    If multiple evidence for same emotion, keep the one with max score.
    """
    query = """
    SELECT ?ev ?emotion ?score WHERE {
        ?fo pl:hasEvidence ?ev .
        ?ev pl:emotion ?emotion .
        ?ev pl:score ?score .
    }
    """
    results = g.query(query, initNs={"pl": PL}, initBindings={"fo": frame_occ})

    evidence_map: Dict[str, Tuple[URIRef, Decimal]] = {}

    for row in results:
        emotion_uri = row.emotion
        # Extract local name from URI
        emotion_name = str(emotion_uri).split("#")[-1]
        score = Decimal(str(row.score))
        ev_uri = row.ev

        # Keep max score for each emotion
        if emotion_name not in evidence_map or score > evidence_map[emotion_name][1]:
            evidence_map[emotion_name] = (ev_uri, score)

    return evidence_map


def infer_dyads(
    g: Graph, frame_occ: URIRef, evidence_map: Dict[str, Tuple[URIRef, Decimal]], threshold: Decimal
) -> List[Tuple[str, Decimal, URIRef, URIRef]]:
    """
    Infer dyads for a FrameOccurrence based on evidence.
    Returns list of (dyad_name, dyad_score, ev1_uri, ev2_uri) for successful inferences.
    """
    inferred = []

    for dyad_name, (e1_name, e2_name) in DYADS.items():
        # Check if both component emotions have evidence
        if e1_name not in evidence_map or e2_name not in evidence_map:
            continue

        ev1_uri, score1 = evidence_map[e1_name]
        ev2_uri, score2 = evidence_map[e2_name]

        # Both scores must meet threshold
        if score1 < threshold or score2 < threshold:
            continue

        # Dyad score is min of component scores
        dyad_score = min(score1, score2)
        inferred.append((dyad_name, dyad_score, ev1_uri, ev2_uri))

    return inferred


def materialize_inference(
    g: Graph,
    frame_occ: URIRef,
    dyad_name: str,
    dyad_score: Decimal,
    ev1: URIRef,
    ev2: URIRef,
    threshold: Decimal,
) -> None:
    """
    Add inferred dyad evidence to the graph.

    Adds:
    - pl:satisfies link from FrameOccurrence to dyad
    - New DyadEvidence node with score, derivedFrom, method
    - pl:hasEvidence link from FrameOccurrence to new evidence
    """
    dyad_uri = PL[dyad_name]

    # (A) Add satisfies
    g.add((frame_occ, PL.satisfies, dyad_uri))

    # (B) Create new DyadEvidence node
    new_ev = BNode()
    g.add((new_ev, RDF.type, PL.DyadEvidence))
    g.add((new_ev, PL.emotion, dyad_uri))
    g.add((new_ev, PL.score, Literal(dyad_score, datatype=XSD.decimal)))
    g.add((new_ev, PL.derivedFrom, ev1))
    g.add((new_ev, PL.derivedFrom, ev2))

    # Inference method string
    g.add((new_ev, PL.method, Literal("min-threshold", datatype=XSD.string)))

    # (C) Link evidence to FrameOccurrence
    g.add((frame_occ, PL.hasEvidence, new_ev))


def run_inference(g: Graph, threshold: Decimal) -> Dict[str, Set[str]]:
    """
    Run dyad inference on all FrameOccurrences.
    Returns dict: frame_local_name -> set of inferred dyad names.
    """
    frame_occs = get_frame_occurrences(g)
    print(f"\nFound {len(frame_occs)} FrameOccurrence(s)")

    inference_results: Dict[str, Set[str]] = {}

    for fo in frame_occs:
        fo_name = str(fo).split("#")[-1]
        evidence_map = get_evidence_for_frame(g, fo)

        print(f"\n{fo_name}:")
        print(f"  Evidence: {', '.join(f'{k}={v[1]}' for k, v in evidence_map.items())}")

        inferred = infer_dyads(g, fo, evidence_map, threshold)

        inference_results[fo_name] = set()

        if inferred:
            for dyad_name, dyad_score, ev1, ev2 in inferred:
                print(f"  -> Inferred: {dyad_name} (score={dyad_score})")
                materialize_inference(g, fo, dyad_name, dyad_score, ev1, ev2, threshold)
                inference_results[fo_name].add(dyad_name)
        else:
            print(f"  -> No dyad inferred (threshold={threshold})")

    return inference_results


def run_self_test(results: Dict[str, Set[str]]) -> bool:
    """
    Verify inference results match expected outcomes.
    Returns True if all tests pass, False otherwise.
    """
    print("\n" + "=" * 50)
    print("Running self-test...")
    print("=" * 50)

    expected = {
        "s1": {"Love"},
        "s2": {"Contempt"},
        "s3": {"Aggressiveness"},
        "s4": {"Disapproval"},
        "s5": {"Hope"},
        "s6": set(),  # No dyad expected (Fear below threshold)
    }

    all_passed = True

    for fo_name, expected_dyads in expected.items():
        actual_dyads = results.get(fo_name, set())

        if actual_dyads == expected_dyads:
            status = "PASS"
        else:
            status = "FAIL"
            all_passed = False

        expected_str = ", ".join(expected_dyads) if expected_dyads else "(none)"
        actual_str = ", ".join(actual_dyads) if actual_dyads else "(none)"
        print(f"  {fo_name}: expected [{expected_str}], got [{actual_str}] -> {status}")

    # Special check: Awe should NOT be inferred for s6
    if "Awe" in results.get("s6", set()):
        print(f"  FAIL: Awe was incorrectly inferred for s6 (Fear below threshold)")
        all_passed = False
    else:
        print(f"  PASS: Awe correctly NOT inferred for s6")

    print("=" * 50)
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED!")
    print("=" * 50)

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Plutchik Dyad Inference")
    parser.add_argument("--th", type=float, default=0.4, help="Threshold (default: 0.4)")
    parser.add_argument("--out", type=str, default="output/out.ttl", help="Output file path")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to data file (default: data/sample.ttl)")
    args = parser.parse_args()

    threshold = Decimal(str(args.th))

    # Determine base directory (script is in scripts/)
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    print(f"Plutchik Dyad Inference")
    print(f"Threshold: {threshold}")
    print(f"Base directory: {base_dir}")
    if args.data:
        print(f"Data file: {args.data}")
    print("-" * 50)

    # Load graph
    g = load_graph(base_dir, data_file=args.data)

    # Run inference
    results = run_inference(g, threshold)

    # Output
    out_path = base_dir / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Add ontology IRI declaration for Protege compatibility
    g.add((OUTPUT_ONTOLOGY, RDF.type, OWL.Ontology))
    g.add((OUTPUT_ONTOLOGY, RDFS.label, Literal("EFO Plutchik Dyad Inference Results")))
    g.add((OUTPUT_ONTOLOGY, RDFS.comment, Literal(f"Inferred dyad emotions using min-threshold aggregation (TH={threshold})")))

    print(f"\nWriting output to: {out_path}")
    g.serialize(destination=str(out_path), format="turtle")
    print(f"Output written: {len(g)} triples")

    # Self-test only when using default sample data (expected values differ for experiment data)
    if args.data is None:
        if not run_self_test(results):
            sys.exit(1)

    print("\nDone!")


if __name__ == "__main__":
    main()
