#!/usr/bin/env python3
"""
Step 2: Map 28 GoEmotions scores to 8 Plutchik basic emotion scores.

Two mapping approaches:
  - nrc (default):       NRC EmoLex-based associations
  - handcrafted:         Static JSON mapping table

Aggregation: ``max`` (default) or ``sum``.

Usage:
    python -m experiment.step2_map_plutchik [--method nrc] [--aggregation max]
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

from experiment.config import DATA_DIR, PLUTCHIK_EMOTIONS
from experiment.mappings.nrc_mapping import get_nrc_mapping

INPUT_FILE = DATA_DIR / "classified_scores.jsonl"
OUTPUT_FILE = DATA_DIR / "plutchik_scores.jsonl"

HANDCRAFTED_JSON = Path(__file__).resolve().parent / "mappings" / "goemotion_to_plutchik.json"


def _load_handcrafted_mapping() -> Dict[str, List[str]]:
    """Load the handcrafted Plutchik -> GoEmotions mapping and invert it."""
    with open(HANDCRAFTED_JSON, encoding="utf-8") as f:
        plutchik_to_go = json.load(f)
    # Invert: goemotion_label -> [plutchik_emotions]
    go_to_plutchik: Dict[str, List[str]] = {}
    for plutchik_emo, go_labels in plutchik_to_go.items():
        for gl in go_labels:
            go_to_plutchik.setdefault(gl, []).append(plutchik_emo)
    return go_to_plutchik


def _build_nrc_go_to_plutchik() -> Dict[str, List[str]]:
    """NRC mapping is already goemotion_label -> [plutchik_emotions]."""
    return get_nrc_mapping()


def map_scores(
    go_scores: Dict[str, float],
    go_to_plutchik: Dict[str, List[str]],
    aggregation: str = "max",
) -> Dict[str, float]:
    """Aggregate 28 GoEmotions scores into 8 Plutchik scores.

    For each Plutchik emotion, collect GoEmotions scores that map to it,
    then apply ``max`` or ``sum`` aggregation.
    """
    # Collect contributions per Plutchik emotion
    buckets: Dict[str, List[float]] = {e: [] for e in PLUTCHIK_EMOTIONS}

    for go_label, score in go_scores.items():
        mapped_emotions = go_to_plutchik.get(go_label, [])
        for emo in mapped_emotions:
            if emo in buckets:
                buckets[emo].append(score)

    # Aggregate
    result: Dict[str, float] = {}
    for emo in PLUTCHIK_EMOTIONS:
        values = buckets[emo]
        if not values:
            result[emo] = 0.0
        elif aggregation == "max":
            result[emo] = max(values)
        elif aggregation == "sum":
            result[emo] = min(sum(values), 1.0)  # clamp to [0, 1]
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")

    return result


def main(method: str = "nrc", aggregation: str = "max") -> Path:
    """Run mapping and write JSONL output.

    Returns the path to the written JSONL file.
    """
    print(f"Step 2: Mapping 28→8 (method={method}, aggregation={aggregation})")

    # Build mapping
    if method == "nrc":
        go_to_plutchik = _build_nrc_go_to_plutchik()
    elif method == "handcrafted":
        go_to_plutchik = _load_handcrafted_mapping()
    else:
        raise ValueError(f"Unknown method: {method}")

    # Process JSONL
    count = 0
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(INPUT_FILE, encoding="utf-8") as in_f, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for line in in_f:
            record = json.loads(line)
            go_scores = record["scores"]
            plutchik_scores = map_scores(go_scores, go_to_plutchik, aggregation)

            out_record = {
                "id": record["id"],
                "text": record["text"],
                "plutchik_scores": plutchik_scores,
                "go_scores": go_scores,
                "gold_labels": record["gold_labels"],
            }
            out_f.write(json.dumps(out_record, ensure_ascii=False) + "\n")
            count += 1

    print(f"  Mapped {count} samples → {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Map GoEmotions to Plutchik")
    parser.add_argument("--method", choices=["nrc", "handcrafted"], default="nrc",
                        help="Mapping method (default: nrc)")
    parser.add_argument("--aggregation", choices=["max", "sum"], default="max",
                        help="Aggregation function (default: max)")
    args = parser.parse_args()
    main(method=args.method, aggregation=args.aggregation)
