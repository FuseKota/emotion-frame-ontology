#!/usr/bin/env python3
"""
GoEmotions experiment pipeline orchestrator.

Runs all steps in sequence with optional skip flags.

Usage:
    python -m experiment.run_pipeline [--n 2000] [--seed 42] [--skip-download] [--skip-classify]
    python -m experiment.run_pipeline --n 10   # smoke test
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from experiment.config import DATA_DIR, OUTPUT_DIR, ROOT_DIR


def _check_output(path: Path, step_name: str) -> None:
    """Verify an output file exists after a step."""
    if not path.exists():
        print(f"ERROR: {step_name} did not produce {path}")
        sys.exit(1)
    print(f"  OK: {path} exists")


def main():
    parser = argparse.ArgumentParser(description="GoEmotions experiment pipeline")
    parser.add_argument("--n", type=int, default=2000, help="Number of samples (default: 2000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--batch-size", type=int, default=32, help="Classification batch size")
    parser.add_argument("--method", choices=["nrc", "handcrafted"], default="nrc",
                        help="Mapping method (default: nrc)")
    parser.add_argument("--aggregation", choices=["max", "sum"], default="max",
                        help="Aggregation function (default: max)")
    parser.add_argument("--score-threshold", type=float, default=0.01,
                        help="Min score for RDF Evidence (default: 0.01)")
    parser.add_argument("--th", type=float, default=0.4,
                        help="Dyad inference threshold (default: 0.4)")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip Step 0 (use existing CSV)")
    parser.add_argument("--skip-classify", action="store_true",
                        help="Skip Step 1 (use existing JSONL)")
    parser.add_argument("--skip-rdf-inference", action="store_true",
                        help="Skip Step 3b (RDF-based inference via run_inference.py)")
    parser.add_argument("--skip-semeval", action="store_true",
                        help="Skip Step 4b (SemEval consistency)")
    args = parser.parse_args()

    t0 = time.time()

    print("=" * 60)
    print("GoEmotions Experiment Pipeline")
    print("=" * 60)
    print(f"  n={args.n}  seed={args.seed}  method={args.method}")
    print(f"  aggregation={args.aggregation}  th={args.th}")
    print()

    # -- Step 0: Download -----------------------------------------------
    goemotion_csv = DATA_DIR / "goemotion_subset.csv"
    if args.skip_download and goemotion_csv.exists():
        print("[Step 0] Skipped (--skip-download)")
    else:
        from experiment.step0_download_data import main as step0
        step0(n=args.n, seed=args.seed)
    _check_output(goemotion_csv, "Step 0")
    print()

    # -- Step 1: Classify -----------------------------------------------
    classified_jsonl = DATA_DIR / "classified_scores.jsonl"
    if args.skip_classify and classified_jsonl.exists():
        print("[Step 1] Skipped (--skip-classify)")
    else:
        from experiment.step1_classify import main as step1
        step1(batch_size=args.batch_size)
    _check_output(classified_jsonl, "Step 1")
    print()

    # -- Step 2: Map to Plutchik ----------------------------------------
    plutchik_jsonl = DATA_DIR / "plutchik_scores.jsonl"
    from experiment.step2_map_plutchik import main as step2
    step2(method=args.method, aggregation=args.aggregation)
    _check_output(plutchik_jsonl, "Step 2")
    print()

    # -- Step 3: Convert to RDF -----------------------------------------
    experiment_ttl = DATA_DIR / "experiment_data.ttl"
    from experiment.step3_to_rdf import main as step3
    step3(score_threshold=args.score_threshold)
    _check_output(experiment_ttl, "Step 3")
    print()

    # -- Step 3b: RDF-based Dyad inference via run_inference.py ----------
    if not args.skip_rdf_inference:
        print("[Step 3b] Running RDF inference via scripts/run_inference.py")
        inference_out = OUTPUT_DIR / "inference_out.ttl"
        cmd = [
            sys.executable, str(ROOT_DIR / "scripts" / "run_inference.py"),
            "--data", str(experiment_ttl),
            "--th", str(args.th),
            "--out", str(inference_out.relative_to(ROOT_DIR)),
        ]
        result = subprocess.run(cmd, cwd=str(ROOT_DIR))
        if result.returncode != 0:
            print(f"WARNING: run_inference.py exited with code {result.returncode}")
        else:
            _check_output(inference_out, "Step 3b")
        print()

    # -- Step 4: Evaluate -----------------------------------------------
    from experiment.step4_evaluate import main as step4
    step4(silver_th=args.th)
    _check_output(OUTPUT_DIR / "evaluation_report.json", "Step 4")
    print()

    # -- Step 4b: SemEval consistency -----------------------------------
    if not args.skip_semeval:
        from experiment.step4b_semeval_consistency import main as step4b
        step4b(n=args.n, th=args.th, batch_size=args.batch_size)
        _check_output(OUTPUT_DIR / "semeval_consistency.json", "Step 4b")
        print()

    # -- Step 5: Mapping comparison -------------------------------------
    from experiment.step5_compare_mappings import main as step5
    step5(th=args.th)
    _check_output(OUTPUT_DIR / "mapping_comparison.json", "Step 5")
    print()

    # -- Step 6: Visualize ----------------------------------------------
    from experiment.step6_visualize import main as step6
    step6()
    print()

    elapsed = time.time() - t0
    print("=" * 60)
    print(f"Pipeline complete in {elapsed:.1f}s")
    print(f"  Report:  {OUTPUT_DIR / 'evaluation_report.json'}")
    print(f"  CSV:     {OUTPUT_DIR / 'threshold_sweep_results.csv'}")
    if not args.skip_semeval:
        print(f"  SemEval: {OUTPUT_DIR / 'semeval_consistency.json'}")
    print(f"  Figures: {OUTPUT_DIR / 'figures/'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
