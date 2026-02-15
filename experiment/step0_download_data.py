#!/usr/bin/env python3
"""
Step 0: Download GoEmotions subset.

Uses the `datasets` library to fetch google-research-datasets/go_emotions
and extract a reproducible random subset.

Usage:
    python -m experiment.step0_download_data [--n 2000] [--seed 42]
"""

import argparse
import csv
from pathlib import Path

from datasets import load_dataset

from experiment.config import DATA_DIR

# GoEmotions label names (index-aligned with the dataset's `labels` field)
GOEMOTION_LABEL_NAMES = [
    "admiration", "amusement", "anger", "annoyance", "approval",
    "caring", "confusion", "curiosity", "desire", "disappointment",
    "disapproval", "disgust", "embarrassment", "excitement", "fear",
    "gratitude", "grief", "joy", "love", "nervousness",
    "neutral", "optimism", "pride", "realization", "relief",
    "remorse", "sadness", "surprise",
]

OUTPUT_FILE = DATA_DIR / "goemotion_subset.csv"


def main(n: int = 2000, seed: int = 42) -> Path:
    """Download GoEmotions and write a subset to CSV.

    Returns the path to the written CSV file.
    """
    print(f"Step 0: Downloading GoEmotions (n={n}, seed={seed})")

    ds = load_dataset("google-research-datasets/go_emotions", "simplified")
    train = ds["train"]

    # Shuffle and take subset
    subset = train.shuffle(seed=seed).select(range(min(n, len(train))))
    print(f"  Selected {len(subset)} samples from {len(train)} training examples")

    # Write CSV
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "text", "gold_labels"])

        for row in subset:
            label_indices = row["labels"]
            label_names = [GOEMOTION_LABEL_NAMES[i] for i in label_indices]
            writer.writerow([row["id"], row["text"], ",".join(label_names)])

    print(f"  Written to: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download GoEmotions subset")
    parser.add_argument("--n", type=int, default=2000, help="Number of samples (default: 2000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()
    main(n=args.n, seed=args.seed)
