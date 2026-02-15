#!/usr/bin/env python3
"""
Step 6: Generate all experiment figures.

Produces 6 publication-quality PNG figures from experiment outputs.

Usage:
    python -m experiment.step6_visualize              # generate all
    python -m experiment.step6_visualize --only 1 3   # generate fig 1 and 3
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from experiment.config import (
    DATA_DIR, DYAD_NAMES, DYADS, FOCUS_DYADS, DYAD_CONSISTENCY_MAP,
    OUTPUT_DIR, PLUTCHIK_EMOTIONS,
)

FIGURES_DIR = OUTPUT_DIR / "figures"

# Consistent style
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
})


# ---------------------------------------------------------------------------
# Figure 1: Threshold sweep F1 curves
# ---------------------------------------------------------------------------
def fig1_threshold_sweep():
    """Macro-F1 and Micro-F1 vs threshold."""
    df = pd.read_csv(OUTPUT_DIR / "threshold_sweep_results.csv")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(df["threshold"], df["macro_f1"], "o-", label="Macro-F1", color="#2196F3")
    ax.plot(df["threshold"], df["micro_f1"], "s-", label="Micro-F1", color="#4CAF50")
    ax.axvline(x=0.4, color="gray", linestyle="--", alpha=0.6, label="TH = 0.4")
    ax.set_xlabel("Threshold")
    ax.set_ylabel("F1 Score")
    ax.set_title("Threshold Sensitivity: Macro-F1 and Micro-F1")
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3)

    out = FIGURES_DIR / "threshold_sweep_f1.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 1] {out}")


# ---------------------------------------------------------------------------
# Figure 2: Dyad distribution bar chart
# ---------------------------------------------------------------------------
def fig2_dyad_distribution():
    """Horizontal bar chart of silver dyad counts."""
    with open(OUTPUT_DIR / "evaluation_report.json") as f:
        report = json.load(f)

    counts = report["silver_dyad_counts"]
    n = report["n_samples"]

    # Sort by count descending
    sorted_dyads = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    names = [d for d, _ in sorted_dyads]
    values = [c for _, c in sorted_dyads]

    colors = ["#E53935" if v == 0 else "#2196F3" for v in values]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.barh(names, values, color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("Count")
    ax.set_title(f"Dyad Distribution (N={n}, TH=0.4)")

    # Annotate counts and percentages
    for bar, val in zip(bars, values):
        pct = val / n * 100
        label = f"{val} ({pct:.1f}%)" if val > 0 else "0"
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                label, va="center", fontsize=9)

    ax.set_xlim(0, max(values) * 1.25)

    out = FIGURES_DIR / "dyad_distribution.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 2] {out}")


# ---------------------------------------------------------------------------
# Figure 3: Component co-occurrence scatter plots
# ---------------------------------------------------------------------------
def fig3_score_cooccurrence():
    """2x2 scatter plots: component emotion co-occurrence."""
    # Load Plutchik scores
    scores: List[Dict[str, float]] = []
    with open(DATA_DIR / "plutchik_scores.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            scores.append(rec["plutchik_scores"])

    pairs = [
        ("Fear", "Surprise", "Awe"),
        ("Anger", "Anticipation", "Aggressiveness"),
        ("Joy", "Trust", "Love"),
        ("Anticipation", "Joy", "Optimism"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(9, 8))
    th = 0.4

    for ax, (e1, e2, dyad) in zip(axes.flat, pairs):
        x = [s[e1] for s in scores]
        y = [s[e2] for s in scores]

        # Count in inference region
        both_above = sum(1 for a, b in zip(x, y) if a >= th and b >= th)

        ax.scatter(x, y, alpha=0.15, s=8, color="#2196F3", edgecolors="none")
        ax.axvline(x=th, color="red", linestyle="--", alpha=0.5)
        ax.axhline(y=th, color="red", linestyle="--", alpha=0.5)

        # Shade inference region
        ax.fill_between([th, 1.0], th, 1.0, alpha=0.08, color="red")

        ax.set_xlabel(e1)
        ax.set_ylabel(e2)
        ax.set_title(f"{dyad} ({e1}+{e2})")
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)

        ax.text(0.95, 0.95, f"n={both_above}",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=10, color="red", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.8))

    fig.suptitle("Component Emotion Co-occurrence (TH=0.4 region shaded)", y=1.02)
    fig.tight_layout()

    out = FIGURES_DIR / "score_cooccurrence.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 3] {out}")


# ---------------------------------------------------------------------------
# Figure 4: Per-Dyad F1 heatmap
# ---------------------------------------------------------------------------
def fig4_per_dyad_heatmap():
    """Heatmap of F1 scores: dyads (rows) x thresholds (columns)."""
    df = pd.read_csv(OUTPUT_DIR / "threshold_sweep_results.csv")

    thresholds = df["threshold"].tolist()
    f1_cols = [c for c in df.columns if c.startswith("f1_")]
    dyad_labels = [c.replace("f1_", "") for c in f1_cols]

    matrix = df[f1_cols].values.T  # (n_dyads, n_thresholds)

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)

    ax.set_xticks(range(len(thresholds)))
    ax.set_xticklabels([f"{t:.2f}" for t in thresholds], rotation=45)
    ax.set_yticks(range(len(dyad_labels)))
    ax.set_yticklabels(dyad_labels)
    ax.set_xlabel("Threshold")
    ax.set_title("Per-Dyad F1 Score (silver TH=0.4)")

    # Annotate cells
    for i in range(len(dyad_labels)):
        for j in range(len(thresholds)):
            val = matrix[i, j]
            color = "white" if val < 0.5 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=7, color=color)

    fig.colorbar(im, ax=ax, label="F1")
    fig.tight_layout()

    out = FIGURES_DIR / "per_dyad_heatmap.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 4] {out}")


# ---------------------------------------------------------------------------
# Figure 5: SemEval effect sizes
# ---------------------------------------------------------------------------
def fig5_semeval_effect_sizes():
    """Bar chart of Mann-Whitney effect sizes from SemEval consistency."""
    with open(OUTPUT_DIR / "semeval_consistency.json") as f:
        data = json.load(f)

    checks = data["consistency_checks"]

    dyads = []
    effect_sizes = []
    p_values = []
    labels = []

    for dyad, emotions in checks.items():
        for emo, stats in emotions.items():
            r = stats.get("effect_size_r")
            p = stats.get("mannwhitney_p")
            n_present = stats.get("n_dyad_present", 0)
            if r is not None and n_present >= 5:
                dyads.append(dyad)
                effect_sizes.append(r)
                p_values.append(p)
                labels.append(f"{dyad}\n({emo})")

    if not dyads:
        print("  [Fig 5] Skipped (no data with n>=5)")
        return

    # Sort by effect size
    order = np.argsort(effect_sizes)[::-1]
    labels = [labels[i] for i in order]
    effect_sizes = [effect_sizes[i] for i in order]
    p_values = [p_values[i] for i in order]

    colors = ["#2196F3" if p < 0.01 else "#BDBDBD" for p in p_values]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(range(len(labels)), effect_sizes, color=colors)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Effect Size (rank-biserial r)")
    ax.set_title("SemEval-2018 Consistency: Mann-Whitney Effect Sizes")
    ax.axvline(x=0, color="black", linewidth=0.5)

    # Annotate p-values
    for i, (bar, p) in enumerate(zip(bars, p_values)):
        p_str = f"p={p:.1e}" if p < 0.01 else f"p={p:.3f}"
        sig = " **" if p < 0.01 else ""
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
                f"{p_str}{sig}", va="center", fontsize=8)

    ax.set_xlim(min(min(effect_sizes) - 0.1, -0.4), max(effect_sizes) + 0.25)
    ax.grid(True, axis="x", alpha=0.3)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#2196F3", label="p < 0.01"),
        Patch(facecolor="#BDBDBD", label="p >= 0.01"),
    ]
    ax.legend(handles=legend_elements, loc="lower right")

    fig.tight_layout()

    out = FIGURES_DIR / "semeval_effect_sizes.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 5] {out}")


# ---------------------------------------------------------------------------
# Figure 6: Mapping comparison
# ---------------------------------------------------------------------------
def fig6_mapping_comparison():
    """Grouped bar chart: NRC vs Handcrafted dyad counts."""
    comparison_file = OUTPUT_DIR / "mapping_comparison.json"
    if not comparison_file.exists():
        print("  [Fig 6] Skipped (run step5_compare_mappings first)")
        return

    with open(comparison_file) as f:
        data = json.load(f)

    nrc_counts = data["dyad_counts"]["nrc"]
    hc_counts = data["dyad_counts"]["handcrafted"]

    x = np.arange(len(DYAD_NAMES))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width / 2, [nrc_counts[d] for d in DYAD_NAMES],
                   width, label="NRC EmoLex", color="#2196F3")
    bars2 = ax.bar(x + width / 2, [hc_counts[d] for d in DYAD_NAMES],
                   width, label="Handcrafted", color="#FF9800")

    ax.set_xticks(x)
    ax.set_xticklabels(DYAD_NAMES, rotation=45, ha="right")
    ax.set_ylabel("Dyad Count")
    ax.set_title(f"NRC vs Handcrafted Mapping: Dyad Detection (TH={data['threshold']})")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)

    # Annotate kappa
    kappa = data["cohen_kappa"]
    ax.text(0.98, 0.95, f"Cohen's kappa = {kappa:.3f}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=10, bbox=dict(boxstyle="round,pad=0.4", fc="lightyellow", ec="gray"))

    fig.tight_layout()

    out = FIGURES_DIR / "mapping_comparison.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 6] {out}")


# ---------------------------------------------------------------------------
# Figure 7: SemEval continuous correlation scatter (Paper Fig 1)
# ---------------------------------------------------------------------------
def fig7_semeval_continuous():
    """2x2 scatter: dyadScore vs SemEval intensity for focus dyads."""
    from scipy import stats as sp_stats

    # Load data
    semeval_continuous_file = OUTPUT_DIR / "semeval_continuous.json"
    if not semeval_continuous_file.exists():
        print("  [Fig 7] Skipped (run step7_semeval_continuous first)")
        return

    with open(semeval_continuous_file) as f:
        report = json.load(f)

    plutchik_cache = DATA_DIR / "semeval_plutchik_cache.jsonl"
    if not plutchik_cache.exists():
        print("  [Fig 7] Skipped (missing semeval_plutchik_cache.jsonl)")
        return

    # Load plutchik cache
    text_to_plutchik: Dict[str, Dict[str, float]] = {}
    with open(plutchik_cache, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            text_to_plutchik[rec["text"]] = rec["plutchik_scores"]

    # Load SemEval intensities
    semeval_cache_dir = DATA_DIR / "semeval_cache"
    text_to_intensities: Dict[str, Dict[str, float]] = {}
    for emo in ["anger", "fear", "joy", "sadness"]:
        cache = semeval_cache_dir / f"semeval_ei_reg_{emo}.jsonl"
        if not cache.exists():
            continue
        with open(cache, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                text = rec["text"]
                if text not in text_to_intensities:
                    text_to_intensities[text] = {}
                text_to_intensities[text][emo] = rec["intensity"]

    # Focus dyad -> semeval emotion pairs
    panels = []
    for dyad in FOCUS_DYADS:
        emos = DYAD_CONSISTENCY_MAP.get(dyad, [])
        if emos:
            panels.append((dyad, emos[0]))

    fig, axes = plt.subplots(2, 2, figsize=(10, 9))

    for ax, (dyad, semeval_emo) in zip(axes.flat, panels):
        e1, e2 = DYADS[dyad]
        xs, ys = [], []
        for text, plutchik in text_to_plutchik.items():
            intensity = text_to_intensities.get(text, {}).get(semeval_emo)
            if intensity is None:
                continue
            dscore = min(plutchik.get(e1, 0.0), plutchik.get(e2, 0.0))
            xs.append(dscore)
            ys.append(intensity)

        xs = np.array(xs)
        ys = np.array(ys)

        ax.scatter(xs, ys, alpha=0.12, s=6, color="#2196F3", edgecolors="none")

        # Regression line + CI
        if len(xs) > 10:
            # Linear fit for visual
            slope, intercept = np.polyfit(xs, ys, 1)
            x_line = np.linspace(xs.min(), xs.max(), 100)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, color="#E53935", linewidth=2, label="OLS fit")

            # Bootstrap CI for regression line
            rng = np.random.default_rng(42)
            y_boots = np.zeros((200, len(x_line)))
            for b in range(200):
                idx = rng.integers(0, len(xs), size=len(xs))
                s_, i_ = np.polyfit(xs[idx], ys[idx], 1)
                y_boots[b] = s_ * x_line + i_
            ci_lo = np.percentile(y_boots, 2.5, axis=0)
            ci_hi = np.percentile(y_boots, 97.5, axis=0)
            ax.fill_between(x_line, ci_lo, ci_hi, alpha=0.15, color="#E53935")

        # Get stats from report
        res = report.get("results", {}).get(dyad, {}).get(semeval_emo, {})
        rho = res.get("spearman_rho", 0)
        ci = res.get("spearman_ci_95", [0, 0])
        pr_auc = res.get("pr_auc", {}).get("0.5")

        annotation = f"rho={rho:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]"
        if pr_auc is not None:
            annotation += f"\nPR-AUC(0.5)={pr_auc:.3f}"
        annotation += f"\nn={len(xs)}"

        ax.text(0.97, 0.97, annotation, transform=ax.transAxes,
                ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))

        ax.set_xlabel(f"dyadScore ({dyad})")
        ax.set_ylabel(f"SemEval intensity ({semeval_emo})")
        ax.set_title(f"{dyad} / {semeval_emo}")
        ax.set_xlim(-0.02, max(xs.max() * 1.1, 0.5) if len(xs) > 0 else 1.0)
        ax.set_ylim(-0.02, 1.05)
        ax.grid(True, alpha=0.2)

    fig.suptitle("Construct Validity: dyadScore vs SemEval-2018 Intensity", y=1.01)
    fig.tight_layout()

    out = FIGURES_DIR / "semeval_continuous_correlation.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 7] {out}")


# ---------------------------------------------------------------------------
# Figure 8: Incremental value (Paper Fig 2)
# ---------------------------------------------------------------------------
def fig8_incremental_value():
    """Grouped bar chart: R-squared comparison across 3 models for focus dyads."""
    incr_file = OUTPUT_DIR / "incremental_value.json"
    if not incr_file.exists():
        print("  [Fig 8] Skipped (run step8_incremental_value first)")
        return

    with open(incr_file) as f:
        data = json.load(f)

    results = data["results"]
    labels = []
    r2_m1 = []
    r2_m2 = []
    r2_m3 = []
    partial_corrs = []
    delta_sigs = []

    for dyad in FOCUS_DYADS:
        if dyad not in results:
            continue
        for emo, res in results[dyad].items():
            if res.get("skipped"):
                continue
            ols = res.get("ols", {})
            m1 = ols.get("model1_components", {})
            m2 = ols.get("model2_dyadscore", {})
            m3 = ols.get("model3_interaction", {})

            labels.append(f"{dyad}\n({emo})")
            r2_m1.append(m1.get("r2", 0))
            r2_m2.append(m2.get("r2", 0))
            r2_m3.append(m3.get("r2", 0))
            partial_corrs.append(res.get("partial_corr", 0))
            delta_sigs.append(m2.get("f_p", 1) < 0.05)

    if not labels:
        print("  [Fig 8] Skipped (no results)")
        return

    x = np.arange(len(labels))
    width = 0.25

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5),
                                     gridspec_kw={"width_ratios": [2, 1]})

    # Left panel: grouped R² bars
    bars1 = ax1.bar(x - width, r2_m1, width, label="M1: comp1 + comp2",
                    color="#BDBDBD")
    bars2 = ax1.bar(x, r2_m2, width, label="M2: + dyadScore",
                    color="#2196F3")
    bars3 = ax1.bar(x + width, r2_m3, width, label="M3: + comp1*comp2",
                    color="#FF9800")

    # Delta R² annotations
    for i in range(len(labels)):
        dr2 = r2_m2[i] - r2_m1[i]
        sig_mark = "*" if delta_sigs[i] else ""
        ax1.annotate(
            f"+{dr2:.4f}{sig_mark}",
            xy=(x[i], r2_m2[i]),
            xytext=(0, 8), textcoords="offset points",
            ha="center", fontsize=8, color="#2196F3", fontweight="bold",
        )

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.set_ylabel("R-squared")
    ax1.set_title("OLS Model Comparison")
    ax1.legend(fontsize=8, loc="upper left")
    ax1.grid(True, axis="y", alpha=0.3)

    # Right panel: partial correlations
    colors = ["#4CAF50" if p > 0 else "#E53935" for p in partial_corrs]
    ax2.barh(range(len(labels)), partial_corrs, color=colors)
    ax2.set_yticks(range(len(labels)))
    ax2.set_yticklabels(labels, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("Partial Correlation")
    ax2.set_title("dyadScore | (comp1, comp2)")
    ax2.axvline(x=0, color="black", linewidth=0.5)
    ax2.grid(True, axis="x", alpha=0.3)

    for i, pc in enumerate(partial_corrs):
        ax2.text(pc + 0.005 if pc >= 0 else pc - 0.005,
                 i, f"{pc:.4f}", va="center",
                 ha="left" if pc >= 0 else "right", fontsize=8)

    fig.suptitle("Incremental Value: dyadScore Beyond Component Scores", y=1.01)
    fig.tight_layout()

    out = FIGURES_DIR / "incremental_value.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 8] {out}")


# ---------------------------------------------------------------------------
# Figure 9: Ontology QA dashboard (Paper Fig 4)
# ---------------------------------------------------------------------------
def fig9_ontology_qa():
    """2-panel dashboard: SHACL results + CQ pass/fail grid."""
    qa_file = OUTPUT_DIR / "ontology_qa.json"
    if not qa_file.exists():
        print("  [Fig 9] Skipped (run step9_ontology_qa first)")
        return

    with open(qa_file) as f:
        data = json.load(f)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left panel: KPI summary bars
    summary = data["summary"]
    kpi_names = [
        "SHACL\nViolations/1K",
        "derivedFrom\nCompleteness",
        "Score\nSoundness",
    ]
    kpi_values = [
        summary.get("violations_per_1k", 0),
        summary.get("derivedFrom_completeness", 0),
        summary.get("score_soundness", 0),
    ]
    # Normalize: violations should be inverted (lower is better)
    kpi_display = [
        1.0 - min(kpi_values[0] / 10, 1.0),  # 0 violations = 1.0
        kpi_values[1],
        kpi_values[2],
    ]
    colors = ["#4CAF50" if v >= 0.95 else "#FF9800" if v >= 0.8 else "#E53935"
              for v in kpi_display]

    bars = ax1.bar(kpi_names, kpi_display, color=colors, edgecolor="white", linewidth=1.5)
    for bar, raw_val, disp_val in zip(bars, kpi_values, kpi_display):
        label = f"{raw_val}" if raw_val < 1 else f"{raw_val:.1%}"
        if kpi_names[0].startswith("SHACL"):
            label = f"{kpi_values[0]:.1f}"
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                 label, ha="center", va="bottom", fontsize=10, fontweight="bold")

    # Correct labels
    ax1.text(bars[0].get_x() + bars[0].get_width() / 2, bars[0].get_height() + 0.02,
             f"{kpi_values[0]:.1f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax1.text(bars[1].get_x() + bars[1].get_width() / 2, bars[1].get_height() + 0.02,
             f"{kpi_values[1]:.1%}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax1.text(bars[2].get_x() + bars[2].get_width() / 2, bars[2].get_height() + 0.02,
             f"{kpi_values[2]:.1%}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax1.set_ylim(0, 1.2)
    ax1.set_title("Quality KPIs")
    ax1.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)
    ax1.set_ylabel("Score (1.0 = perfect)")

    # Right panel: CQ pass/fail grid
    cq_results = data.get("competency_queries", {}).get("queries", [])
    if cq_results:
        cq_names = [q["file"].replace(".rq", "").replace("_", "\n") for q in cq_results]
        cq_pass = [1 if q["pass"] else 0 for q in cq_results]
        cq_rows = [q.get("n_rows", 0) for q in cq_results]

        colors_cq = ["#4CAF50" if p else "#E53935" for p in cq_pass]
        y_pos = range(len(cq_names))
        ax2.barh(y_pos, [1] * len(cq_names), color=colors_cq, edgecolor="white",
                 linewidth=1.5)
        ax2.set_yticks(list(y_pos))
        ax2.set_yticklabels(cq_names, fontsize=8)
        ax2.invert_yaxis()

        for i, (passed, n_rows) in enumerate(zip(cq_pass, cq_rows)):
            label = f"PASS ({n_rows} rows)" if passed else f"FAIL ({n_rows} rows)"
            ax2.text(0.5, i, label, ha="center", va="center",
                     fontsize=9, fontweight="bold", color="white")

        ax2.set_xlim(0, 1)
        ax2.set_xticks([])
        ax2.set_title("Competency Queries")

        # Summary
        n_pass = sum(cq_pass)
        n_total = len(cq_pass)
        ax2.text(0.5, -0.08, f"Score: {n_pass}/{n_total}",
                 transform=ax2.transAxes, ha="center", fontsize=11, fontweight="bold")

    fig.suptitle("Ontology Quality Assurance Dashboard", y=1.01)
    fig.tight_layout()

    out = FIGURES_DIR / "ontology_qa_dashboard.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"  [Fig 9] {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
ALL_FIGURES = {
    1: ("Threshold sweep F1", fig1_threshold_sweep),
    2: ("Dyad distribution", fig2_dyad_distribution),
    3: ("Score co-occurrence", fig3_score_cooccurrence),
    4: ("Per-dyad F1 heatmap", fig4_per_dyad_heatmap),
    5: ("SemEval effect sizes", fig5_semeval_effect_sizes),
    6: ("Mapping comparison", fig6_mapping_comparison),
    7: ("SemEval continuous correlation", fig7_semeval_continuous),
    8: ("Incremental value", fig8_incremental_value),
    9: ("Ontology QA dashboard", fig9_ontology_qa),
}


def main(only: List[int] = None):
    """Generate experiment figures."""
    print("Step 6: Generating figures")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    targets = only if only else list(ALL_FIGURES.keys())

    for fig_num in targets:
        if fig_num not in ALL_FIGURES:
            print(f"  Unknown figure: {fig_num}")
            continue
        name, func = ALL_FIGURES[fig_num]
        try:
            func()
        except Exception as e:
            print(f"  [Fig {fig_num}] ERROR: {e}")

    print(f"  Done. Figures in: {FIGURES_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate experiment figures")
    parser.add_argument("--only", type=int, nargs="+", default=None,
                        help="Generate only specified figures (e.g. --only 1 3)")
    args = parser.parse_args()
    main(only=args.only)
