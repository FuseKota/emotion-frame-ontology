#!/usr/bin/env python3
"""
Step 10: Aggregation function comparison study.

Compares 7 aggregation functions for dyad score computation against
SemEval-2018 EI-reg intensity as external ground truth.

Aggregation functions:
  1. Min (current)       — Gödel t-norm
  2. Product             — independent probability
  3. Geometric Mean      — balanced ensemble
  4. Harmonic Mean       — F1-like structure
  5. Łukasiewicz         — implicit threshold t-norm
  6. Power Mean (p=-2)   — between min and harmonic
  7. OWA (0.3/0.7)       — ordered weighted average

Evaluation:
  - Primary: Spearman rho (continuous dyadScore vs SemEval intensity)
  - Auxiliary: PR-AUC at t=0.5
  - Auxiliary: Partial correlation controlling for comp1, comp2
  - Descriptive: mean, std, zero-rate of dyadScore

Generates: output/experiment/aggregation_study.json

Usage:
    python -m experiment.step10_aggregation_study
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

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

OUTPUT_FILE = OUTPUT_DIR / "aggregation_study.json"
PLUTCHIK_CACHE = DATA_DIR / "semeval_plutchik_cache.jsonl"
SEMEVAL_CACHE_DIR = DATA_DIR / "semeval_cache"

SEMEVAL_EMOTIONS = ["anger", "fear", "joy", "sadness"]


# ---------------------------------------------------------------------------
# Aggregation functions
# ---------------------------------------------------------------------------

def _agg_min(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Min (Gödel t-norm) — current default."""
    return np.minimum(a, b)


def _agg_product(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Product t-norm."""
    return a * b


def _agg_geometric_mean(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Geometric mean."""
    return np.sqrt(a * b)


def _agg_harmonic_mean(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Harmonic mean (F1-like). Returns 0 when either is 0."""
    denom = a + b
    result = np.where(denom > 0, 2 * a * b / denom, 0.0)
    return result


def _agg_lukasiewicz(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Łukasiewicz t-norm: max(0, a + b - 1)."""
    return np.maximum(0.0, a + b - 1.0)


def _agg_power_mean_neg2(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Power mean with p=-2. Returns 0 when either is 0."""
    p = -2.0
    mask = (a > 0) & (b > 0)
    result = np.zeros_like(a)
    result[mask] = ((a[mask] ** p + b[mask] ** p) / 2.0) ** (1.0 / p)
    return result


def _agg_owa(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """OWA with weights (0.3, 0.7): 0.3*max + 0.7*min."""
    return 0.3 * np.maximum(a, b) + 0.7 * np.minimum(a, b)


AGGREGATION_FUNCTIONS: Dict[str, Callable] = {
    "min": _agg_min,
    "product": _agg_product,
    "geometric_mean": _agg_geometric_mean,
    "harmonic_mean": _agg_harmonic_mean,
    "lukasiewicz": _agg_lukasiewicz,
    "power_mean_neg2": _agg_power_mean_neg2,
    "owa_0.3_0.7": _agg_owa,
}


# ---------------------------------------------------------------------------
# Reused utilities
# ---------------------------------------------------------------------------

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
    """Apply Holm-Bonferroni correction."""
    m = len(p_values)
    if m == 0:
        return []
    order = np.argsort(p_values)
    adjusted = np.empty(m)
    for rank, idx in enumerate(order):
        adjusted[idx] = p_values[idx] * (m - rank)
    sorted_adj = adjusted[order]
    for i in range(1, m):
        if sorted_adj[i] < sorted_adj[i - 1]:
            sorted_adj[i] = sorted_adj[i - 1]
    adjusted[order] = sorted_adj
    return [min(float(p), 1.0) for p in adjusted]


def _partial_corr(
    x: np.ndarray, y: np.ndarray, covariates: np.ndarray,
) -> float:
    """Spearman partial correlation (rank-based)."""
    n = len(x)
    rx = stats.rankdata(x)
    ry = stats.rankdata(y)
    rc = np.column_stack([stats.rankdata(covariates[:, j])
                          for j in range(covariates.shape[1])])
    rc_aug = np.column_stack([np.ones(n), rc])
    try:
        beta_x = np.linalg.lstsq(rc_aug, rx, rcond=None)[0]
        beta_y = np.linalg.lstsq(rc_aug, ry, rcond=None)[0]
    except np.linalg.LinAlgError:
        return 0.0
    res_x = rx - rc_aug @ beta_x
    res_y = ry - rc_aug @ beta_y
    denom = np.sqrt(np.sum(res_x**2) * np.sum(res_y**2))
    if denom == 0:
        return 0.0
    return float(np.sum(res_x * res_y) / denom)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_data() -> Tuple[
    List[str],
    List[Dict[str, float]],
    Dict[str, Dict[str, float]],
]:
    """Load Plutchik cache and SemEval intensity data."""
    if not PLUTCHIK_CACHE.exists():
        raise FileNotFoundError(
            f"Plutchik cache not found: {PLUTCHIK_CACHE}\n"
            "Run step7_semeval_continuous first."
        )

    texts: List[str] = []
    plutchik_list: List[Dict[str, float]] = []
    with open(PLUTCHIK_CACHE, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            texts.append(rec["text"])
            plutchik_list.append(rec["plutchik_scores"])

    text_to_intensities: Dict[str, Dict[str, float]] = {}
    for emo in SEMEVAL_EMOTIONS:
        cache_path = SEMEVAL_CACHE_DIR / f"semeval_ei_reg_{emo}.jsonl"
        if not cache_path.exists():
            continue
        with open(cache_path, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                text = rec["text"]
                if text not in text_to_intensities:
                    text_to_intensities[text] = {}
                text_to_intensities[text][emo] = rec["intensity"]

    return texts, plutchik_list, text_to_intensities


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> Path:
    """Run aggregation function comparison study."""
    print("Step 10: Aggregation function comparison study")

    texts, plutchik_list, text_to_intensities = _load_data()
    print(f"  Loaded {len(texts)} texts with Plutchik scores")

    agg_names = list(AGGREGATION_FUNCTIONS.keys())
    all_p_values: List[float] = []
    p_value_keys: List[Tuple[str, str, str]] = []  # (agg, dyad, emo)

    # Store per-aggregation results
    results: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for agg_name, agg_fn in AGGREGATION_FUNCTIONS.items():
        print(f"\n  --- {agg_name} ---")
        agg_results: Dict[str, Dict[str, Any]] = {}

        for dyad in FOCUS_DYADS:
            related_emotions = DYAD_CONSISTENCY_MAP.get(dyad, [])
            if not related_emotions:
                continue

            e1, e2 = DYADS[dyad]
            dyad_result: Dict[str, Any] = {}

            for semeval_emo in related_emotions:
                # Gather aligned arrays
                c1_list: List[float] = []
                c2_list: List[float] = []
                intensity_list: List[float] = []

                for i, text in enumerate(texts):
                    intensity = text_to_intensities.get(text, {}).get(semeval_emo)
                    if intensity is None:
                        continue
                    ps = plutchik_list[i]
                    c1_list.append(ps.get(e1, 0.0))
                    c2_list.append(ps.get(e2, 0.0))
                    intensity_list.append(intensity)

                n = len(intensity_list)
                if n < 10:
                    dyad_result[semeval_emo] = {"n": n, "skipped": True}
                    continue

                c1_arr = np.array(c1_list)
                c2_arr = np.array(c2_list)
                i_arr = np.array(intensity_list)

                # Compute dyadScore with this aggregation
                d_arr = agg_fn(c1_arr, c2_arr)

                # --- Spearman rho ---
                rho, p_val = stats.spearmanr(d_arr, i_arr)
                ci_lo, ci_hi = _bootstrap_spearman_ci(
                    d_arr, i_arr,
                    rng=np.random.default_rng(42),
                )
                all_p_values.append(p_val)
                p_value_keys.append((agg_name, dyad, semeval_emo))

                # --- PR-AUC at t=0.5 ---
                y_true = (i_arr > 0.5).astype(int)
                n_pos = int(y_true.sum())
                if 0 < n_pos < n:
                    pr_auc = float(average_precision_score(y_true, d_arr))
                else:
                    pr_auc = None

                # --- Partial correlation ---
                covariates = np.column_stack([c1_arr, c2_arr])
                pcorr = _partial_corr(d_arr, i_arr, covariates)

                # --- Descriptive stats ---
                zero_rate = float(np.mean(d_arr == 0))

                check: Dict[str, Any] = {
                    "n": n,
                    "spearman_rho": float(rho),
                    "spearman_p": float(p_val),
                    "spearman_ci_95": [ci_lo, ci_hi],
                    "pr_auc_0.5": pr_auc,
                    "partial_corr": pcorr,
                    "dyad_score_mean": float(np.mean(d_arr)),
                    "dyad_score_std": float(np.std(d_arr)),
                    "dyad_score_zero_rate": zero_rate,
                    "comp1": e1,
                    "comp2": e2,
                }

                dyad_result[semeval_emo] = check
                print(
                    f"    {dyad}/{semeval_emo}: "
                    f"rho={rho:+.4f}  "
                    f"pcorr={pcorr:+.4f}  "
                    f"zero_rate={zero_rate:.2%}"
                )

            if dyad_result:
                agg_results[dyad] = dyad_result

        results[agg_name] = agg_results

    # --- Holm correction across ALL tests ---
    adjusted = _holm_correction(all_p_values)
    for (agg_name, dyad, emo), p_adj in zip(p_value_keys, adjusted):
        if dyad in results[agg_name] and emo in results[agg_name][dyad]:
            results[agg_name][dyad][emo]["spearman_p_holm"] = p_adj

    # --- Build summary table ---
    summary: List[Dict[str, Any]] = []
    for agg_name in agg_names:
        for dyad in FOCUS_DYADS:
            if dyad not in results.get(agg_name, {}):
                continue
            for emo, res in results[agg_name][dyad].items():
                if res.get("skipped"):
                    continue
                summary.append({
                    "aggregation": agg_name,
                    "dyad": dyad,
                    "semeval_emotion": emo,
                    "n": res["n"],
                    "spearman_rho": res["spearman_rho"],
                    "ci_95": res["spearman_ci_95"],
                    "p_holm": res.get("spearman_p_holm"),
                    "pr_auc_0.5": res["pr_auc_0.5"],
                    "partial_corr": res["partial_corr"],
                    "dyad_score_mean": res["dyad_score_mean"],
                    "dyad_score_std": res["dyad_score_std"],
                    "dyad_score_zero_rate": res["dyad_score_zero_rate"],
                })

    # --- Build comparison matrix (agg x dyad) ---
    comparison_matrix: Dict[str, Dict[str, float]] = {}
    for agg_name in agg_names:
        row: Dict[str, float] = {}
        for dyad in FOCUS_DYADS:
            if dyad not in results.get(agg_name, {}):
                continue
            # Use first (or only) SemEval emotion
            emos = DYAD_CONSISTENCY_MAP.get(dyad, [])
            if emos and emos[0] in results[agg_name][dyad]:
                res = results[agg_name][dyad][emos[0]]
                if not res.get("skipped"):
                    row[dyad] = res["spearman_rho"]
        comparison_matrix[agg_name] = row

    # --- Find best aggregation per dyad ---
    best_per_dyad: Dict[str, Dict[str, Any]] = {}
    for dyad in FOCUS_DYADS:
        best_rho = -float("inf")
        best_agg = "min"
        for agg_name in agg_names:
            rho = comparison_matrix.get(agg_name, {}).get(dyad)
            if rho is not None and rho > best_rho:
                best_rho = rho
                best_agg = agg_name
        min_rho = comparison_matrix.get("min", {}).get(dyad)
        best_per_dyad[dyad] = {
            "best_aggregation": best_agg,
            "best_rho": best_rho,
            "min_rho": min_rho,
            "improvement": best_rho - min_rho if min_rho is not None else None,
        }

    # --- Mean rho across focus dyads per aggregation ---
    mean_rho_per_agg: Dict[str, float] = {}
    for agg_name in agg_names:
        rhos = [v for v in comparison_matrix.get(agg_name, {}).values()
                if v is not None]
        mean_rho_per_agg[agg_name] = float(np.mean(rhos)) if rhos else 0.0

    # --- Build output ---
    output: Dict[str, Any] = {
        "n_aggregation_functions": len(agg_names),
        "aggregation_functions": agg_names,
        "focus_dyads": FOCUS_DYADS,
        "n_bootstrap": N_BOOTSTRAP,
        "n_tests_holm": len(all_p_values),
        "results": results,
        "summary_table": summary,
        "comparison_matrix": comparison_matrix,
        "mean_rho_per_aggregation": mean_rho_per_agg,
        "best_per_dyad": best_per_dyad,
    }

    # --- Write ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Written to: {OUTPUT_FILE}")

    # --- Print comparison table ---
    print("\n  === Comparison Matrix (Spearman rho) ===")
    header = f"  {'Aggregation':20s}"
    for dyad in FOCUS_DYADS:
        header += f"  {dyad:>12s}"
    header += f"  {'Mean':>8s}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for agg_name in agg_names:
        row_str = f"  {agg_name:20s}"
        for dyad in FOCUS_DYADS:
            rho = comparison_matrix.get(agg_name, {}).get(dyad)
            row_str += f"  {rho:+12.4f}" if rho is not None else f"  {'N/A':>12s}"
        row_str += f"  {mean_rho_per_agg[agg_name]:+8.4f}"
        if agg_name == "min":
            row_str += "  (baseline)"
        print(row_str)

    print("\n  === Best per Dyad ===")
    for dyad, info in best_per_dyad.items():
        imp = info["improvement"]
        imp_str = f"  delta={imp:+.4f}" if imp is not None else ""
        print(
            f"  {dyad:15s}: {info['best_aggregation']:20s}  "
            f"rho={info['best_rho']:+.4f}{imp_str}"
        )

    return OUTPUT_FILE


if __name__ == "__main__":
    main()
