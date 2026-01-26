#!/usr/bin/env python3
"""
Threshold Sensitivity Analysis Script

Performs threshold sweep analysis for Plutchik dyad inference.
Reference: EFO-PlutchikDyad paper, Section VII (E2)

Outputs Table III format results:
- Situations w/ >=1 dyad
- Mean dyads/sit.
- Mean dyadScore

Usage:
    python scripts/threshold_sweep.py [--data DATA_FILE]
"""

import argparse
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional, Tuple

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

# Namespaces
PL = Namespace("http://example.org/efo/plutchik#")
FSCHEMA = Namespace("https://w3id.org/framester/schema/")

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

# Default threshold sweep values
DEFAULT_THRESHOLDS = [0.3, 0.4, 0.5, 0.6]


@dataclass
class SweepResult:
    """Results for a single threshold value."""
    threshold: float
    situations_with_dyad: int
    total_situations: int
    total_dyads_inferred: int
    dyad_scores: List[float]

    @property
    def pct_with_dyad(self) -> float:
        """Percentage of situations with at least one dyad."""
        if self.total_situations == 0:
            return 0.0
        return (self.situations_with_dyad / self.total_situations) * 100

    @property
    def mean_dyads_per_situation(self) -> float:
        """Mean number of dyads per situation."""
        if self.total_situations == 0:
            return 0.0
        return self.total_dyads_inferred / self.total_situations

    @property
    def mean_dyad_score(self) -> Optional[float]:
        """Mean dyadScore across all inferred dyads."""
        if not self.dyad_scores:
            return None
        return mean(self.dyad_scores)


def load_graph(base_dir: Path, data_file: Optional[str] = None) -> Graph:
    """Load required TTL files into a graph."""
    g = Graph()
    g.bind("pl", PL)
    g.bind("fschema", FSCHEMA)

    # Load ontology module
    ontology_path = base_dir / "modules" / "EFO-PlutchikDyad.ttl"
    if ontology_path.exists():
        g.parse(ontology_path, format="turtle")

    # Load data file
    if data_file:
        data_path = Path(data_file)
        if not data_path.is_absolute():
            data_path = base_dir / data_file
    else:
        data_path = base_dir / "data" / "sample.ttl"

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    g.parse(data_path, format="turtle")
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


def get_evidence_for_frame(g: Graph, frame_occ: URIRef) -> Dict[str, Decimal]:
    """
    Get emotion evidence scores for a FrameOccurrence.
    Returns dict: emotion_local_name -> max_score
    """
    query = """
    SELECT ?emotion ?score WHERE {
        ?fo pl:hasEvidence ?ev .
        ?ev pl:emotion ?emotion .
        ?ev pl:score ?score .
        FILTER NOT EXISTS { ?ev a pl:DyadEvidence }
    }
    """
    results = g.query(query, initNs={"pl": PL}, initBindings={"fo": frame_occ})

    evidence_map: Dict[str, Decimal] = {}

    for row in results:
        emotion_uri = row.emotion
        emotion_name = str(emotion_uri).split("#")[-1]
        score = Decimal(str(row.score))

        # Keep max score for each emotion
        if emotion_name not in evidence_map or score > evidence_map[emotion_name]:
            evidence_map[emotion_name] = score

    return evidence_map


def infer_dyads_for_threshold(
    evidence_map: Dict[str, Decimal],
    threshold: Decimal
) -> List[Tuple[str, Decimal]]:
    """
    Infer dyads based on evidence and threshold.
    Returns list of (dyad_name, dyad_score).
    """
    inferred = []

    for dyad_name, (e1_name, e2_name) in DYADS.items():
        if e1_name not in evidence_map or e2_name not in evidence_map:
            continue

        score1 = evidence_map[e1_name]
        score2 = evidence_map[e2_name]

        # Both scores must meet threshold
        if score1 < threshold or score2 < threshold:
            continue

        dyad_score = min(score1, score2)
        inferred.append((dyad_name, dyad_score))

    return inferred


def run_sweep(g: Graph, thresholds: List[float]) -> List[SweepResult]:
    """
    Run threshold sweep analysis.
    Returns results for each threshold value.
    """
    frame_occs = get_frame_occurrences(g)

    # Pre-compute evidence for all situations
    situation_evidence = {}
    for fo in frame_occs:
        fo_name = str(fo).split("#")[-1]
        situation_evidence[fo_name] = get_evidence_for_frame(g, fo)

    results = []

    for th in thresholds:
        threshold = Decimal(str(th))

        situations_with_dyad = 0
        total_dyads = 0
        all_scores = []

        for fo_name, evidence_map in situation_evidence.items():
            inferred = infer_dyads_for_threshold(evidence_map, threshold)

            if inferred:
                situations_with_dyad += 1
                total_dyads += len(inferred)
                all_scores.extend([float(score) for _, score in inferred])

        results.append(SweepResult(
            threshold=th,
            situations_with_dyad=situations_with_dyad,
            total_situations=len(frame_occs),
            total_dyads_inferred=total_dyads,
            dyad_scores=all_scores,
        ))

    return results


def print_table(results: List[SweepResult]) -> None:
    """Print results in Table III format."""
    print("\n" + "=" * 70)
    print("Threshold Sensitivity Analysis (Table III)")
    print("=" * 70)
    print()

    # Header
    print(f"{'TH':<8} {'Sit. w/ ≥1 dyad':<20} {'Mean dyads/sit.':<18} {'Mean dyadScore':<15}")
    print("-" * 70)

    for r in results:
        sit_str = f"{r.situations_with_dyad}/{r.total_situations} ({r.pct_with_dyad:.1f}%)"
        mean_dyads = f"{r.mean_dyads_per_situation:.2f}"
        mean_score = f"{r.mean_dyad_score:.3f}" if r.mean_dyad_score is not None else "N/A"

        print(f"{r.threshold:<8.1f} {sit_str:<20} {mean_dyads:<18} {mean_score:<15}")

    print("-" * 70)
    print()


def print_detailed_breakdown(g: Graph, thresholds: List[float]) -> None:
    """Print detailed breakdown per situation."""
    frame_occs = get_frame_occurrences(g)

    print("\n" + "=" * 70)
    print("Detailed Breakdown by Situation")
    print("=" * 70)

    for fo in frame_occs:
        fo_name = str(fo).split("#")[-1]
        evidence_map = get_evidence_for_frame(g, fo)

        print(f"\n{fo_name}:")
        evidence_str = ", ".join(f"{k}={v}" for k, v in sorted(evidence_map.items()))
        print(f"  Evidence: {evidence_str}")

        for th in thresholds:
            threshold = Decimal(str(th))
            inferred = infer_dyads_for_threshold(evidence_map, threshold)

            if inferred:
                dyads_str = ", ".join(f"{name}({score})" for name, score in inferred)
            else:
                dyads_str = "(none)"

            print(f"  TH={th}: {dyads_str}")


def export_csv(results: List[SweepResult], output_path: Path) -> None:
    """Export results to CSV format."""
    with open(output_path, "w") as f:
        f.write("threshold,situations_with_dyad,total_situations,pct_with_dyad,mean_dyads_per_sit,mean_dyad_score\n")
        for r in results:
            mean_score = r.mean_dyad_score if r.mean_dyad_score is not None else ""
            f.write(f"{r.threshold},{r.situations_with_dyad},{r.total_situations},{r.pct_with_dyad:.2f},{r.mean_dyads_per_situation:.3f},{mean_score}\n")
    print(f"CSV exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Threshold Sensitivity Analysis")
    parser.add_argument("--data", type=str, help="Path to data file (default: data/sample.ttl)")
    parser.add_argument("--thresholds", type=str, default="0.3,0.4,0.5,0.6",
                        help="Comma-separated threshold values (default: 0.3,0.4,0.5,0.6)")
    parser.add_argument("--detailed", action="store_true", help="Show detailed breakdown")
    parser.add_argument("--csv", type=str, help="Export results to CSV file")
    args = parser.parse_args()

    # Parse thresholds
    thresholds = [float(x.strip()) for x in args.thresholds.split(",")]

    # Determine base directory
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    print("Threshold Sensitivity Analysis")
    print(f"Reference: EFO-PlutchikDyad paper, Section VII (E2)")
    print(f"Thresholds: {thresholds}")
    print("-" * 50)

    # Load graph
    g = load_graph(base_dir, args.data)

    # Run sweep
    results = run_sweep(g, thresholds)

    # Print table
    print_table(results)

    # Detailed breakdown if requested
    if args.detailed:
        print_detailed_breakdown(g, thresholds)

    # Export CSV if requested
    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.is_absolute():
            csv_path = base_dir / args.csv
        export_csv(results, csv_path)

    print("Done!")


if __name__ == "__main__":
    main()
