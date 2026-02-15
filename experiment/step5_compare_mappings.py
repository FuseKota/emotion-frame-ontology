#!/usr/bin/env python3
"""
Step 5: Compare NRC vs Handcrafted mapping approaches.

Runs both mapping strategies on the same classified scores (Step 1 output)
and compares dyad detection counts, Plutchik score distributions, and
inter-method agreement.

Usage:
    python -m experiment.step5_compare_mappings [--th 0.4]
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from sklearn.metrics import cohen_kappa_score

from experiment.config import (
    DATA_DIR,
    DYAD_NAMES,
    DYADS,
    OUTPUT_DIR,
    PLUTCHIK_EMOTIONS,
)
from experiment.step2_map_plutchik import (
    _build_nrc_go_to_plutchik,
    _load_handcrafted_mapping,
    map_scores,
)

INPUT_FILE = DATA_DIR / "classified_scores.jsonl"
OUTPUT_FILE = OUTPUT_DIR / "mapping_comparison.json"


def _load_go_scores() -> List[Dict[str, Any]]:
    """Load classified GoEmotions scores."""
    records = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def _infer_dyad_labels(
    plutchik_scores: Dict[str, float], threshold: float
) -> Dict[str, int]:
    labels = {}
    for dyad, (e1, e2) in DYADS.items():
        s1 = plutchik_scores.get(e1, 0.0)
        s2 = plutchik_scores.get(e2, 0.0)
        labels[dyad] = 1 if s1 >= threshold and s2 >= threshold else 0
    return labels


def main(th: float = 0.4) -> Path:
    """Run mapping comparison and write JSON output."""
    print(f"Step 5: Comparing NRC vs Handcrafted mappings (th={th})")

    records = _load_go_scores()
    n = len(records)
    print(f"  Loaded {n} samples")

    nrc_map = _build_nrc_go_to_plutchik()
    hc_map = _load_handcrafted_mapping()

    # Compute Plutchik scores for both methods
    nrc_plutchik_all: List[Dict[str, float]] = []
    hc_plutchik_all: List[Dict[str, float]] = []

    for rec in records:
        go_scores = rec["scores"]
        nrc_plutchik_all.append(map_scores(go_scores, nrc_map, "max"))
        hc_plutchik_all.append(map_scores(go_scores, hc_map, "max"))

    # --- Per-emotion score statistics ---
    emotion_stats: Dict[str, Dict[str, Any]] = {}
    for emo in PLUTCHIK_EMOTIONS:
        nrc_vals = [p[emo] for p in nrc_plutchik_all]
        hc_vals = [p[emo] for p in hc_plutchik_all]
        emotion_stats[emo] = {
            "nrc_mean": float(np.mean(nrc_vals)),
            "nrc_std": float(np.std(nrc_vals)),
            "hc_mean": float(np.mean(hc_vals)),
            "hc_std": float(np.std(hc_vals)),
            "nrc_above_th": int(sum(1 for v in nrc_vals if v >= th)),
            "hc_above_th": int(sum(1 for v in hc_vals if v >= th)),
        }

    # --- Dyad detection counts ---
    nrc_dyad_counts: Dict[str, int] = {d: 0 for d in DYAD_NAMES}
    hc_dyad_counts: Dict[str, int] = {d: 0 for d in DYAD_NAMES}
    nrc_labels_flat: List[int] = []
    hc_labels_flat: List[int] = []

    for i in range(n):
        nrc_labels = _infer_dyad_labels(nrc_plutchik_all[i], th)
        hc_labels = _infer_dyad_labels(hc_plutchik_all[i], th)
        for d in DYAD_NAMES:
            nrc_dyad_counts[d] += nrc_labels[d]
            hc_dyad_counts[d] += hc_labels[d]
            nrc_labels_flat.append(nrc_labels[d])
            hc_labels_flat.append(hc_labels[d])

    # --- Cohen's kappa ---
    kappa = float(cohen_kappa_score(nrc_labels_flat, hc_labels_flat))

    # --- Co-occurrence analysis for zero-support dyads ---
    cooccurrence: Dict[str, Dict[str, Any]] = {}
    for dyad, (e1, e2) in DYADS.items():
        for method_name, plutchik_list in [("nrc", nrc_plutchik_all), ("hc", hc_plutchik_all)]:
            key = f"{dyad}_{method_name}"
            e1_vals = [p[e1] for p in plutchik_list]
            e2_vals = [p[e2] for p in plutchik_list]
            both_above = sum(
                1 for a, b in zip(e1_vals, e2_vals) if a >= th and b >= th
            )
            cooccurrence[key] = {
                "e1": e1,
                "e2": e2,
                "method": method_name,
                "e1_above_th": sum(1 for v in e1_vals if v >= th),
                "e2_above_th": sum(1 for v in e2_vals if v >= th),
                "both_above_th": both_above,
            }

    # --- Build report ---
    report: Dict[str, Any] = {
        "n_samples": n,
        "threshold": th,
        "emotion_stats": emotion_stats,
        "dyad_counts": {
            "nrc": nrc_dyad_counts,
            "handcrafted": hc_dyad_counts,
        },
        "cohen_kappa": kappa,
        "cooccurrence": cooccurrence,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n  {'Dyad':<18} {'NRC':>6} {'HC':>6} {'Diff':>6}")
    print(f"  {'-'*36}")
    for d in DYAD_NAMES:
        diff = hc_dyad_counts[d] - nrc_dyad_counts[d]
        sign = "+" if diff > 0 else ""
        print(f"  {d:<18} {nrc_dyad_counts[d]:>6} {hc_dyad_counts[d]:>6} {sign}{diff:>5}")
    print(f"\n  Cohen's kappa: {kappa:.4f}")
    print(f"  Written to: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare NRC vs Handcrafted mappings")
    parser.add_argument("--th", type=float, default=0.4, help="Threshold (default: 0.4)")
    args = parser.parse_args()
    main(th=args.th)
