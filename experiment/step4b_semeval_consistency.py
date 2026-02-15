#!/usr/bin/env python3
"""
Step 4b: SemEval-2018 Task 1 (Affect in Tweets) consistency evaluation.

Uses the EI-reg (emotion intensity regression) subtask data which has
continuous intensity scores for anger, fear, joy, and sadness.

We run the same classification → Plutchik mapping → dyad inference pipeline
on SemEval texts and then check whether inferred dyads are **consistent**
with the known emotion intensities.

Consistency checks
------------------
1. Spearman correlation between related intensity and dyad presence.
2. Mann-Whitney U test: intensity distribution for dyad-present vs absent.

Usage:
    python -m experiment.step4b_semeval_consistency [--n 1000] [--th 0.4]
"""

import argparse
import csv
import json
import os
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

from experiment.config import DATA_DIR, DYADS, OUTPUT_DIR, PLUTCHIK_EMOTIONS
from experiment.mappings.nrc_mapping import get_nrc_mapping
from experiment.step2_map_plutchik import map_scores

SEMEVAL_OUTPUT = OUTPUT_DIR / "semeval_consistency.json"
SEMEVAL_CACHE_DIR = DATA_DIR / "semeval_cache"
SEMEVAL_RAW_DIR = DATA_DIR / "semeval_raw"

# SemEval-2018 EI-reg emotions → Plutchik mapping
SEMEVAL_EMOTIONS = ["anger", "fear", "joy", "sadness"]
SEMEVAL_TO_PLUTCHIK = {
    "anger": "Anger",
    "fear": "Fear",
    "joy": "Joy",
    "sadness": "Sadness",
}

# Dyad → relevant SemEval emotion(s) for consistency checks
DYAD_CONSISTENCY_MAP: Dict[str, List[str]] = {
    "Love": ["joy"],
    "Submission": ["fear"],
    "Awe": ["fear"],
    "Disapproval": ["sadness"],
    "Remorse": ["sadness"],
    "Contempt": ["anger"],
    "Aggressiveness": ["anger"],
    "Optimism": ["joy"],
    "Hope": [],
    "Pride": ["anger", "joy"],
}


def _load_semeval_data() -> Dict[str, List[Dict[str, Any]]]:
    """Load SemEval-2018 EI-reg data from local TSV files.

    Reads ``data/experiment/semeval_raw/EI-reg-En-{emo}-{split}.txt`` files
    (train + dev).  Falls back to JSONL cache if present.

    Returns dict: emotion -> list of {text, intensity} records.
    """
    SEMEVAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    all_data: Dict[str, List[Dict[str, Any]]] = {}

    for emo in SEMEVAL_EMOTIONS:
        cache_path = SEMEVAL_CACHE_DIR / f"semeval_ei_reg_{emo}.jsonl"

        # Try cache first
        if cache_path.exists():
            records: List[Dict[str, Any]] = []
            with open(cache_path, encoding="utf-8") as f:
                for line in f:
                    records.append(json.loads(line))
            all_data[emo] = records
            continue

        # Read raw TSV files (train + dev)
        records = []
        for split in ("train", "dev"):
            tsv_path = SEMEVAL_RAW_DIR / f"EI-reg-En-{emo}-{split}.txt"
            if not tsv_path.exists():
                raise FileNotFoundError(
                    f"SemEval data not found: {tsv_path}\n"
                    f"Download with:\n"
                    f"  mkdir -p {SEMEVAL_RAW_DIR}\n"
                    f"  curl -sL https://raw.githubusercontent.com/cbaziotis/"
                    f"ntua-slp-semeval2018/master/datasets/task1/EI-reg/"
                    f"EI-reg-En-{emo}-{split}.txt -o {tsv_path}"
                )
            with open(tsv_path, encoding="utf-8") as f:
                header = f.readline()  # skip header
                for line in f:
                    parts = line.rstrip("\n").split("\t")
                    if len(parts) < 4:
                        continue
                    records.append({
                        "id": parts[0],
                        "text": parts[1],
                        "intensity": float(parts[3]),
                    })
        print(f"  Loaded {len(records)} records for {emo}")

        # Write cache
        with open(cache_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        all_data[emo] = records

    return all_data


def _classify_and_map(
    texts: List[str],
    batch_size: int = 32,
) -> List[Dict[str, float]]:
    """Run GoEmotions classification + Plutchik mapping on texts.

    Returns list of Plutchik score dicts (one per text).
    """
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_name = "SamLowe/roberta-base-go_emotions"
    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        else "cpu"
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.to(device)
    model.eval()

    label_names = list(model.config.id2label.values())
    go_to_plutchik = get_nrc_mapping()

    all_plutchik_scores: List[Dict[str, float]] = []

    for start in range(0, len(texts), batch_size):
        batch_texts = texts[start : start + batch_size]
        encodings = tokenizer(
            batch_texts, padding=True, truncation=True,
            max_length=512, return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            logits = model(**encodings).logits
            probs = torch.sigmoid(logits).cpu().tolist()

        for prob_vec in probs:
            go_scores = {name: p for name, p in zip(label_names, prob_vec)}
            plutchik = map_scores(go_scores, go_to_plutchik, aggregation="max")
            all_plutchik_scores.append(plutchik)

    return all_plutchik_scores


def _infer_dyads_binary(
    plutchik_scores: Dict[str, float],
    threshold: float,
) -> Dict[str, int]:
    """Return binary dyad labels using min-threshold rule."""
    labels = {}
    for dyad, (e1, e2) in DYADS.items():
        s1 = plutchik_scores.get(e1, 0.0)
        s2 = plutchik_scores.get(e2, 0.0)
        labels[dyad] = 1 if s1 >= threshold and s2 >= threshold else 0
    return labels


def main(n: int = 1000, th: float = 0.4, batch_size: int = 32) -> Path:
    """Run SemEval-2018 consistency evaluation.

    Returns the path to the output JSON.
    """
    print(f"Step 4b: SemEval-2018 consistency (n={n}, th={th})")

    # 1. Get SemEval data
    semeval_data = _load_semeval_data()

    # 2. Collect all unique texts across emotions with their intensities
    text_to_intensities: Dict[str, Dict[str, float]] = {}
    for emo, records in semeval_data.items():
        for rec in records[:n]:
            text = rec["text"]
            if text not in text_to_intensities:
                text_to_intensities[text] = {}
            text_to_intensities[text][emo] = rec["intensity"]

    all_texts = list(text_to_intensities.keys())
    print(f"  Unique texts: {len(all_texts)}")

    # 3. Classify and map to Plutchik
    print("  Running classification + mapping...")
    plutchik_list = _classify_and_map(all_texts, batch_size=batch_size)

    # 4. Infer dyads
    dyad_labels_list = [
        _infer_dyads_binary(ps, th) for ps in plutchik_list
    ]

    # 5. Consistency checks
    results: Dict[str, Any] = {
        "n_texts": len(all_texts),
        "threshold": th,
        "consistency_checks": {},
    }

    for dyad, related_emotions in DYAD_CONSISTENCY_MAP.items():
        if not related_emotions:
            continue

        dyad_check: Dict[str, Any] = {}

        for semeval_emo in related_emotions:
            # Collect pairs: (intensity, dyad_present)
            intensities_present = []
            intensities_absent = []

            for i, text in enumerate(all_texts):
                intensity = text_to_intensities[text].get(semeval_emo)
                if intensity is None:
                    continue

                if dyad_labels_list[i][dyad] == 1:
                    intensities_present.append(intensity)
                else:
                    intensities_absent.append(intensity)

            n_present = len(intensities_present)
            n_absent = len(intensities_absent)

            check: Dict[str, Any] = {
                "n_dyad_present": n_present,
                "n_dyad_absent": n_absent,
            }

            # Spearman correlation (over all samples with this emotion)
            all_int = intensities_present + intensities_absent
            all_dyad = [1] * n_present + [0] * n_absent

            if len(all_int) >= 10:
                rho, p_val = stats.spearmanr(all_int, all_dyad)
                check["spearman_rho"] = float(rho)
                check["spearman_p"] = float(p_val)

            # Mann-Whitney U test
            if n_present >= 5 and n_absent >= 5:
                u_stat, u_p = stats.mannwhitneyu(
                    intensities_present, intensities_absent,
                    alternative="greater",
                )
                check["mannwhitney_u"] = float(u_stat)
                check["mannwhitney_p"] = float(u_p)

                # Effect size (rank-biserial correlation)
                effect = 2 * u_stat / (n_present * n_absent) - 1
                check["effect_size_r"] = float(effect)

            if n_present > 0:
                check["mean_intensity_present"] = float(np.mean(intensities_present))
            if n_absent > 0:
                check["mean_intensity_absent"] = float(np.mean(intensities_absent))

            dyad_check[semeval_emo] = check

        results["consistency_checks"][dyad] = dyad_check

    # 6. Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SEMEVAL_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"  Written to: {SEMEVAL_OUTPUT}")
    return SEMEVAL_OUTPUT


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SemEval-2018 consistency evaluation")
    parser.add_argument("--n", type=int, default=1000,
                        help="Max samples per emotion (default: 1000)")
    parser.add_argument("--th", type=float, default=0.4,
                        help="Dyad inference threshold (default: 0.4)")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch size for classification (default: 32)")
    args = parser.parse_args()
    main(n=args.n, th=args.th, batch_size=args.batch_size)
