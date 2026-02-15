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

from experiment.config import DATA_DIR, DYAD_NAMES, DYADS, OUTPUT_DIR, PLUTCHIK_EMOTIONS

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
# Main
# ---------------------------------------------------------------------------
ALL_FIGURES = {
    1: ("Threshold sweep F1", fig1_threshold_sweep),
    2: ("Dyad distribution", fig2_dyad_distribution),
    3: ("Score co-occurrence", fig3_score_cooccurrence),
    4: ("Per-dyad F1 heatmap", fig4_per_dyad_heatmap),
    5: ("SemEval effect sizes", fig5_semeval_effect_sizes),
    6: ("Mapping comparison", fig6_mapping_comparison),
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
