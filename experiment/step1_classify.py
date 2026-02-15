#!/usr/bin/env python3
"""
Step 1: Classify texts with SamLowe/roberta-base-go_emotions.

Reads the CSV from Step 0 and produces JSONL with 28 emotion scores per text.

Usage:
    python -m experiment.step1_classify [--batch-size 32]
"""

import argparse
import csv
import json
from pathlib import Path

import torch
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from experiment.config import DATA_DIR

INPUT_FILE = DATA_DIR / "goemotion_subset.csv"
OUTPUT_FILE = DATA_DIR / "classified_scores.jsonl"

MODEL_NAME = "SamLowe/roberta-base-go_emotions"


def _get_device() -> torch.device:
    """Pick best available device: CUDA > MPS > CPU."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def main(batch_size: int = 32) -> Path:
    """Run HuggingFace classification and write JSONL output.

    Returns the path to the written JSONL file.
    """
    print(f"Step 1: Classifying with {MODEL_NAME}")

    # Read input CSV
    rows = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    print(f"  Loaded {len(rows)} samples from {INPUT_FILE}")

    # Load model & tokenizer
    device = _get_device()
    print(f"  Device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()

    label_names = list(model.config.id2label.values())

    # Process in batches
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for batch_start in tqdm(range(0, len(rows), batch_size), desc="Classifying"):
            batch_rows = rows[batch_start : batch_start + batch_size]
            texts = [r["text"] for r in batch_rows]

            encodings = tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(device)

            with torch.no_grad():
                logits = model(**encodings).logits
                probs = torch.sigmoid(logits).cpu().tolist()

            for row, prob_vec in zip(batch_rows, probs):
                scores = {name: round(p, 6) for name, p in zip(label_names, prob_vec)}
                record = {
                    "id": row["id"],
                    "text": row["text"],
                    "scores": scores,
                    "gold_labels": row["gold_labels"].split(",") if row["gold_labels"] else [],
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"  Written to: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify with GoEmotions model")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    args = parser.parse_args()
    main(batch_size=args.batch_size)
