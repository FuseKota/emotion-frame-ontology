#!/usr/bin/env python3
"""
Step 7: SemEval-2018 dyadScore continuous evaluation.

Extends the binary evaluation (step4b) with continuous correlation analysis:
  - Spearman rho (dyadScore vs SemEval intensity) with Bootstrap 95% CI
  - PR-AUC at multiple intensity thresholds (0.25, 0.50, 0.75)
  - Holm correction for multiple testing

Generates: output/experiment/semeval_continuous.json
           data/experiment/semeval_plutchik_cache.jsonl (classification cache)

Usage:
    python -m experiment.step7_semeval_continuous [--batch-size 32]
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats
from sklearn.metrics import average_precision_score

from experiment.config import (
    DATA_DIR,
    DYAD_CONSISTENCY_MAP,
    DYADS,
    FOCUS_DYADS,
    N_BOOTSTRAP,
    OUTPUT_DIR,
)

SEMEVAL_OUTPUT = OUTPUT_DIR / "semeval_continuous.json"
PLUTCHIK_CACHE = DATA_DIR / "semeval_plutchik_cache.jsonl"

SEMEVAL_EMOTIONS = ["anger", "fear", "joy", "sadness"]


# ---------------------------------------------------------------------------
# Data loading (reuse step4b helpers)
# ---------------------------------------------------------------------------

def _load_semeval_data() -> Dict[str, List[Dict[str, Any]]]:
    """Load SemEval-2018 EI-reg data (delegated to step4b)."""
    from experiment.step4b_semeval_consistency import _load_semeval_data
    return _load_semeval_data()


def _classify_and_map_cached(
    texts: List[str], batch_size: int = 32,
) -> List[Dict[str, float]]:
    """Classify texts and cache results to semeval_plutchik_cache.jsonl.

    If cache exists and covers all texts, load from cache.
    """
    if PLUTCHIK_CACHE.exists():
        cached: Dict[str, Dict[str, float]] = {}
        with open(PLUTCHIK_CACHE, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                cached[rec["text"]] = rec["plutchik_scores"]
        if all(t in cached for t in texts):
            print(f"  Loaded {len(cached)} cached Plutchik scores")
            return [cached[t] for t in texts]
        print(f"  Cache incomplete ({len(cached)}/{len(texts)}), re-classifying...")

    from experiment.step4b_semeval_consistency import _classify_and_map
    plutchik_list = _classify_and_map(texts, batch_size=batch_size)

    # Write cache
    PLUTCHIK_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLUTCHIK_CACHE, "w", encoding="utf-8") as f:
        for text, scores in zip(texts, plutchik_list):
            f.write(json.dumps(
                {"text": text, "plutchik_scores": scores},
                ensure_ascii=False,
            ) + "\n")
    print(f"  Cached {len(plutchik_list)} Plutchik scores to {PLUTCHIK_CACHE}")

    return plutchik_list


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def _compute_dyad_scores(plutchik: Dict[str, float]) -> Dict[str, float]:
    """Return continuous dyadScore = min(comp1, comp2) for all dyads."""
    return {
        dyad: min(plutchik.get(e1, 0.0), plutchik.get(e2, 0.0))
        for dyad, (e1, e2) in DYADS.items()
    }


def _bootstrap_spearman_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_boot: int = N_BOOTSTRAP,
    alpha: float = 0.05,
    rng: np.random.Generator = None,
) -> Tuple[float, float]:
    """Bootstrap 95% CI for Spearman rho."""
    if rng is None:
        rng = np.random.default_rng(42)
    n = len(x)
    rhos = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        rhos[i] = stats.spearmanr(x[idx], y[idx]).statistic
    lo = np.nanpercentile(rhos, 100 * alpha / 2)
    hi = np.nanpercentile(rhos, 100 * (1 - alpha / 2))
    return float(lo), float(hi)


def _holm_correction(p_values: List[float]) -> List[float]:
    """Apply Holm-Bonferroni correction to a list of p-values.

    Returns adjusted p-values (monotonically non-decreasing).
    """
    m = len(p_values)
    if m == 0:
        return []
    order = np.argsort(p_values)
    adjusted = np.empty(m)
    for rank, idx in enumerate(order):
        adjusted[idx] = p_values[idx] * (m - rank)
    # Enforce monotonicity (step-up)
    sorted_adj = adjusted[order]
    for i in range(1, m):
        if sorted_adj[i] < sorted_adj[i - 1]:
            sorted_adj[i] = sorted_adj[i - 1]
    adjusted[order] = sorted_adj
    return [min(float(p), 1.0) for p in adjusted]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(batch_size: int = 32) -> Path:
    """Run SemEval-2018 continuous evaluation."""
    print("Step 7: SemEval-2018 continuous evaluation (dyadScore vs intensity)")

    # 1. Load SemEval data
    semeval_data = _load_semeval_data()

    # 2. Collect unique texts with their intensities (full dataset, no cap)
    text_to_intensities: Dict[str, Dict[str, float]] = {}
    for emo, records in semeval_data.items():
        for rec in records:
            text = rec["text"]
            if text not in text_to_intensities:
                text_to_intensities[text] = {}
            text_to_intensities[text][emo] = rec["intensity"]

    all_texts = list(text_to_intensities.keys())
    n_unique = len(all_texts)
    print(f"  Unique texts (dedup): {n_unique}")

    # Per-emotion sample counts
    emo_counts = {emo: sum(1 for t in all_texts if emo in text_to_intensities[t])
                  for emo in SEMEVAL_EMOTIONS}
    print(f"  Per-emotion n: {emo_counts}")

    # 3. Classify and map to Plutchik (with caching)
    plutchik_list = _classify_and_map_cached(all_texts, batch_size=batch_size)

    # 4. Compute continuous dyadScores for all samples
    dyad_scores_list = [_compute_dyad_scores(ps) for ps in plutchik_list]

    # 5. Evaluate each Dyad-Emotion pair
    pr_auc_thresholds = [0.25, 0.50, 0.75]
    all_p_values: List[float] = []
    pair_keys: List[Tuple[str, str]] = []
    pair_results: Dict[str, Dict[str, Any]] = {}

    for dyad, related_emotions in DYAD_CONSISTENCY_MAP.items():
        if not related_emotions:
            continue
        dyad_result: Dict[str, Any] = {}
        e1, e2 = DYADS[dyad]

        for semeval_emo in related_emotions:
            # Gather aligned arrays
            d_scores = []
            intensities = []
            comp1_scores = []
            comp2_scores = []
            for i, text in enumerate(all_texts):
                intensity = text_to_intensities[text].get(semeval_emo)
                if intensity is None:
                    continue
                d_scores.append(dyad_scores_list[i][dyad])
                intensities.append(intensity)
                comp1_scores.append(plutchik_list[i].get(e1, 0.0))
                comp2_scores.append(plutchik_list[i].get(e2, 0.0))

            n_samples = len(d_scores)
            if n_samples < 10:
                dyad_result[semeval_emo] = {
                    "n": n_samples,
                    "skipped": True,
                    "reason": "n < 10",
                }
                continue

            d_arr = np.array(d_scores)
            i_arr = np.array(intensities)

            # --- Spearman rho ---
            rho, p_val = stats.spearmanr(d_arr, i_arr)
            ci_lo, ci_hi = _bootstrap_spearman_ci(d_arr, i_arr)
            all_p_values.append(p_val)
            pair_keys.append((dyad, semeval_emo))

            check: Dict[str, Any] = {
                "n": n_samples,
                "spearman_rho": float(rho),
                "spearman_p": float(p_val),
                "spearman_ci_95": [ci_lo, ci_hi],
                "dyad_score_mean": float(np.mean(d_arr)),
                "dyad_score_std": float(np.std(d_arr)),
                "intensity_mean": float(np.mean(i_arr)),
                "intensity_std": float(np.std(i_arr)),
            }

            # --- PR-AUC at multiple thresholds ---
            pr_aucs = {}
            for t in pr_auc_thresholds:
                y_true = (i_arr > t).astype(int)
                n_pos = int(y_true.sum())
                if n_pos == 0 or n_pos == n_samples:
                    pr_aucs[str(t)] = None
                else:
                    pr_aucs[str(t)] = float(
                        average_precision_score(y_true, d_arr)
                    )
            check["pr_auc"] = pr_aucs

            # --- Component score statistics (for incremental value) ---
            check["comp1"] = e1
            check["comp2"] = e2
            check["comp1_mean"] = float(np.mean(comp1_scores))
            check["comp2_mean"] = float(np.mean(comp2_scores))

            dyad_result[semeval_emo] = check

        if dyad_result:
            pair_results[dyad] = dyad_result

    # 6. Holm correction
    adjusted = _holm_correction(all_p_values)
    for (dyad, emo), p_adj in zip(pair_keys, adjusted):
        if dyad in pair_results and emo in pair_results[dyad]:
            pair_results[dyad][emo]["spearman_p_holm"] = p_adj

    # 7. Build output
    output = {
        "n_unique_texts": n_unique,
        "per_emotion_n": emo_counts,
        "n_bootstrap": N_BOOTSTRAP,
        "pr_auc_thresholds": pr_auc_thresholds,
        "n_tests_holm": len(all_p_values),
        "focus_dyads": FOCUS_DYADS,
        "results": pair_results,
    }

    # Summary table for focus dyads
    summary = []
    for dyad in FOCUS_DYADS:
        if dyad not in pair_results:
            continue
        for emo, res in pair_results[dyad].items():
            if res.get("skipped"):
                continue
            summary.append({
                "dyad": dyad,
                "semeval_emotion": emo,
                "n": res["n"],
                "spearman_rho": res["spearman_rho"],
                "ci_95": res["spearman_ci_95"],
                "p_raw": res["spearman_p"],
                "p_holm": res.get("spearman_p_holm"),
                "pr_auc_0.5": res["pr_auc"].get("0.5"),
            })
    output["summary_table"] = summary

    # 8. Write
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SEMEVAL_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Written to: {SEMEVAL_OUTPUT}")

    # Print summary
    print("\n  === Summary (Focus Dyads) ===")
    for row in summary:
        sig = "***" if (row["p_holm"] or 1) < 0.001 else (
            "**" if (row["p_holm"] or 1) < 0.01 else (
                "*" if (row["p_holm"] or 1) < 0.05 else ""))
        print(
            f"  {row['dyad']:15s} / {row['semeval_emotion']:8s}  "
            f"rho={row['spearman_rho']:+.3f}  "
            f"CI=[{row['ci_95'][0]:+.3f}, {row['ci_95'][1]:+.3f}]  "
            f"p(Holm)={row['p_holm']:.2e}  "
            f"PR-AUC(0.5)={row['pr_auc_0.5'] or 'N/A':>5}  "
            f"{sig}"
        )

    return SEMEVAL_OUTPUT


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SemEval-2018 continuous dyadScore evaluation"
    )
    parser.add_argument(
        "--batch-size", type=int, default=32,
        help="Batch size for classification (default: 32)",
    )
    args = parser.parse_args()
    main(batch_size=args.batch_size)
