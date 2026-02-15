#!/usr/bin/env python3
"""
Step 4: Evaluate Dyad inference against silver labels.

Works entirely in Python (JSONL-based) — no RDF round-trip needed.

Silver labels
-------------
A dyad is considered *present* for a sample when **both** component emotion
scores meet or exceed a threshold.

Baselines
---------
1. No-Dyad      — always predict 0  (null hypothesis)
2. Naive-Dyad   — predict 1 if both components > 0.01  (score-agnostic)
3. Score-Aware   — predict 1 if both components >= TH   (proposed method)

Metrics
-------
- Macro-F1, Micro-F1, Precision, Recall (sklearn)
- Threshold sweep: 0.30 .. 0.70 (step 0.05)
- Per-Dyad F1 breakdown (10 dyads)

Usage:
    python -m experiment.step4_evaluate [--silver-th 0.4]
"""

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score

from experiment.config import (
    DATA_DIR,
    DEFAULT_THRESHOLDS,
    DYAD_NAMES,
    DYADS,
    OUTPUT_DIR,
)

INPUT_FILE = DATA_DIR / "plutchik_scores.jsonl"
REPORT_FILE = OUTPUT_DIR / "evaluation_report.json"
SWEEP_CSV = OUTPUT_DIR / "threshold_sweep_results.csv"


def _load_samples() -> List[Dict[str, Any]]:
    """Load Plutchik-scored samples."""
    samples = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            samples.append(json.loads(line))
    return samples


def _infer_dyad_labels(
    plutchik_scores: Dict[str, float],
    threshold: float,
) -> Dict[str, int]:
    """Infer binary dyad labels using min-threshold rule.

    Mirrors the logic of ``run_inference.py:infer_dyads()``.
    """
    labels: Dict[str, int] = {}
    for dyad, (e1, e2) in DYADS.items():
        s1 = plutchik_scores.get(e1, 0.0)
        s2 = plutchik_scores.get(e2, 0.0)
        labels[dyad] = 1 if s1 >= threshold and s2 >= threshold else 0
    return labels


def _build_label_matrix(
    samples: List[Dict[str, Any]],
    threshold: float,
) -> np.ndarray:
    """Build (N, D) binary matrix.  D = len(DYAD_NAMES)."""
    rows = []
    for s in samples:
        labels = _infer_dyad_labels(s["plutchik_scores"], threshold)
        rows.append([labels[d] for d in DYAD_NAMES])
    return np.array(rows, dtype=int)


# -- Baselines ---------------------------------------------------------------

def _no_dyad_predictions(n: int) -> np.ndarray:
    """Baseline: always predict 0."""
    return np.zeros((n, len(DYAD_NAMES)), dtype=int)


def _naive_dyad_predictions(samples: List[Dict[str, Any]]) -> np.ndarray:
    """Baseline: predict 1 if both component scores > 0.01."""
    return _build_label_matrix(samples, threshold=0.01 + 1e-9)


# -- Metrics ------------------------------------------------------------------

def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute classification metrics for multi-label binary arrays."""
    # Handle edge case where all predictions (or all labels) are 0
    if y_true.sum() == 0 and y_pred.sum() == 0:
        return {
            "macro_f1": 1.0,
            "micro_f1": 1.0,
            "macro_precision": 1.0,
            "macro_recall": 1.0,
        }

    return {
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "micro_f1": float(f1_score(y_true, y_pred, average="micro", zero_division=0)),
        "macro_precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def _per_dyad_f1(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute per-dyad F1 scores."""
    result = {}
    for i, dyad in enumerate(DYAD_NAMES):
        result[dyad] = float(
            f1_score(y_true[:, i], y_pred[:, i], zero_division=0)
        )
    return result


# -- Main evaluation ----------------------------------------------------------

def main(silver_th: float = 0.4) -> Path:
    """Run full evaluation and write outputs.

    Returns the path to the evaluation report.
    """
    print(f"Step 4: Evaluation (silver_th={silver_th})")

    samples = _load_samples()
    n = len(samples)
    print(f"  Loaded {n} samples")

    # Silver labels at the reference threshold
    y_silver = _build_label_matrix(samples, silver_th)
    silver_dyad_counts = {
        d: int(y_silver[:, i].sum()) for i, d in enumerate(DYAD_NAMES)
    }
    print(f"  Silver dyad counts (TH={silver_th}): {silver_dyad_counts}")

    # Baselines
    y_no_dyad = _no_dyad_predictions(n)
    y_naive = _naive_dyad_predictions(samples)

    report: Dict[str, Any] = {
        "n_samples": n,
        "silver_threshold": silver_th,
        "silver_dyad_counts": silver_dyad_counts,
    }

    # -- Cross-threshold analysis --
    sweep_rows: List[Dict[str, Any]] = []

    for th_pred in DEFAULT_THRESHOLDS:
        y_pred = _build_label_matrix(samples, th_pred)

        metrics_vs_silver = _compute_metrics(y_silver, y_pred)
        per_dyad = _per_dyad_f1(y_silver, y_pred)

        row = {
            "threshold": th_pred,
            "num_dyads_predicted": int(y_pred.sum()),
            **metrics_vs_silver,
            "per_dyad_f1": per_dyad,
        }
        sweep_rows.append(row)

    report["threshold_sweep"] = sweep_rows

    # Baselines vs silver
    report["baselines"] = {
        "no_dyad": _compute_metrics(y_silver, y_no_dyad),
        "naive_dyad": {
            **_compute_metrics(y_silver, y_naive),
            "num_dyads_predicted": int(y_naive.sum()),
        },
        "score_aware_at_silver_th": {
            **_compute_metrics(y_silver, y_silver),
            "num_dyads_predicted": int(y_silver.sum()),
        },
    }

    # Per-dyad breakdown at silver threshold
    report["per_dyad_f1_at_silver_th"] = _per_dyad_f1(y_silver, y_silver)

    # Write JSON report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Report: {REPORT_FILE}")

    # Write CSV for plotting
    with open(SWEEP_CSV, "w", encoding="utf-8") as f:
        header = [
            "threshold", "num_dyads_predicted",
            "macro_f1", "micro_f1", "macro_precision", "macro_recall",
        ]
        # Add per-dyad columns
        for d in DYAD_NAMES:
            header.append(f"f1_{d}")

        f.write(",".join(header) + "\n")

        for row in sweep_rows:
            values = [
                str(row["threshold"]),
                str(row["num_dyads_predicted"]),
                f"{row['macro_f1']:.4f}",
                f"{row['micro_f1']:.4f}",
                f"{row['macro_precision']:.4f}",
                f"{row['macro_recall']:.4f}",
            ]
            for d in DYAD_NAMES:
                values.append(f"{row['per_dyad_f1'][d]:.4f}")
            f.write(",".join(values) + "\n")

    print(f"  CSV: {SWEEP_CSV}")
    return REPORT_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Dyad inference")
    parser.add_argument("--silver-th", type=float, default=0.4,
                        help="Silver label threshold (default: 0.4)")
    args = parser.parse_args()
    main(silver_th=args.silver_th)
