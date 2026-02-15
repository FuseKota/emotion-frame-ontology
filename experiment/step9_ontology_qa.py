#!/usr/bin/env python3
"""
Step 9: Ontology QA — SHACL validation + Competency Query KPI automation.

Runs SHACL shapes validation and 7 competency queries against the inferred
RDF graph, producing quantitative KPIs for reproducibility and explainability.

KPIs
----
- SHACL: conforms, n_violations, n_warnings, violations_per_1k_triples
- derivedFrom completeness: % DyadEvidence with exactly 2 derivedFrom links
- Score soundness: % dyadScore <= min(comp1, comp2)
- CQ pass/fail for each of 7 competency queries

Generates: output/experiment/ontology_qa.json

Usage:
    python -m experiment.step9_ontology_qa [--inference]
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from rdflib import Graph, Namespace, RDF, Literal
from rdflib.term import URIRef

from experiment.config import OUTPUT_DIR, ROOT_DIR

OUTPUT_FILE = OUTPUT_DIR / "ontology_qa.json"

# Paths
EXPERIMENT_DATA = ROOT_DIR / "data" / "experiment" / "experiment_data.ttl"
INFERENCE_OUT = OUTPUT_DIR / "inference_out.ttl"
ONTOLOGY_MODULE = ROOT_DIR / "modules" / "EFO-PlutchikDyad.ttl"
SHAPES_FILE = ROOT_DIR / "shacl" / "plutchik-dyad-shapes.ttl"
CQ_DIR = ROOT_DIR / "sparql" / "cq"

# Namespaces
PL = Namespace("http://example.org/efo/plutchik#")
FSCHEMA = Namespace("https://w3id.org/framester/schema/")
SH = Namespace("http://www.w3.org/ns/shacl#")


# ---------------------------------------------------------------------------
# Graph loading
# ---------------------------------------------------------------------------

def _load_graph() -> Graph:
    """Load ontology + experiment data + inference output into a single graph."""
    g = Graph()
    g.bind("pl", PL)
    g.bind("fschema", FSCHEMA)

    for path in [ONTOLOGY_MODULE, EXPERIMENT_DATA, INFERENCE_OUT]:
        if path.exists():
            g.parse(str(path), format="turtle")
            print(f"  Loaded: {path.name} ({len(g)} triples cumulative)")
        else:
            print(f"  WARNING: missing {path}")

    return g


# ---------------------------------------------------------------------------
# SHACL validation
# ---------------------------------------------------------------------------

def _run_shacl(g: Graph, use_inference: bool = False) -> Dict[str, Any]:
    """Run SHACL validation and return KPIs."""
    try:
        from pyshacl import validate
    except ImportError:
        return {"error": "pyshacl not installed", "conforms": None}

    sg = Graph()
    sg.parse(str(SHAPES_FILE), format="turtle")

    conforms, results_graph, results_text = validate(
        g,
        shacl_graph=sg,
        inference="rdfs" if use_inference else "none",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False,
    )

    # Count violations and warnings
    n_violations = 0
    n_warnings = 0
    for s, p, o in results_graph.triples((None, SH.resultSeverity, None)):
        if o == SH.Violation:
            n_violations += 1
        elif o == SH.Warning:
            n_warnings += 1

    total_triples = len(g)
    violations_per_1k = (n_violations / total_triples * 1000) if total_triples > 0 else 0

    return {
        "conforms": conforms,
        "n_violations": n_violations,
        "n_warnings": n_warnings,
        "total_triples": total_triples,
        "violations_per_1k_triples": round(violations_per_1k, 3),
    }


# ---------------------------------------------------------------------------
# Competency Queries
# ---------------------------------------------------------------------------

def _run_cq(g: Graph, cq_file: Path) -> Dict[str, Any]:
    """Execute a single CQ and return results summary."""
    query_text = cq_file.read_text(encoding="utf-8")

    try:
        results = g.query(query_text)
        rows = list(results)
        return {
            "file": cq_file.name,
            "n_rows": len(rows),
            "executed": True,
            "error": None,
        }
    except Exception as e:
        return {
            "file": cq_file.name,
            "n_rows": 0,
            "executed": False,
            "error": str(e),
        }


def _run_all_cqs(g: Graph) -> Dict[str, Any]:
    """Run all CQ queries and determine pass/fail."""
    cq_files = sorted(CQ_DIR.glob("*.rq"))
    results: List[Dict[str, Any]] = []

    # Expected behavior per CQ
    expectations = {
        "cq1_list_dyads.rq": {"min_rows": 1, "desc": "List inferred dyads"},
        "cq2_components.rq": {"min_rows": 1, "desc": "Retrieve dyad components"},
        "cq3_explain.rq": {"min_rows": 1, "desc": "Explain dyad via provenance"},
        "cq4_threshold_check.rq": {"min_rows": 0, "desc": "Sub-threshold situations"},
        "cq5_topk.rq": {"min_rows": 1, "desc": "Top-K dyads by score"},
        "cq_missing_provenance.rq": {"max_rows": 0, "desc": "Missing derivedFrom"},
        "cq_score_reconstruction.rq": {"max_rows": 0, "desc": "Min-score mismatches"},
    }

    n_pass = 0
    n_total = 0

    for cq_file in cq_files:
        result = _run_cq(g, cq_file)
        name = cq_file.name
        expect = expectations.get(name, {})
        result["description"] = expect.get("desc", "")

        # Determine pass/fail
        passed = True
        if not result["executed"]:
            passed = False
        elif "max_rows" in expect:
            passed = result["n_rows"] <= expect["max_rows"]
        elif "min_rows" in expect:
            passed = result["n_rows"] >= expect["min_rows"]

        result["pass"] = passed
        results.append(result)
        n_total += 1
        if passed:
            n_pass += 1

    return {
        "queries": results,
        "n_pass": n_pass,
        "n_total": n_total,
        "all_pass": n_pass == n_total,
    }


# ---------------------------------------------------------------------------
# Additional KPIs
# ---------------------------------------------------------------------------

def _derived_from_completeness(g: Graph) -> Dict[str, Any]:
    """Check that every DyadEvidence has exactly 2 derivedFrom links."""
    dyad_evidences = list(g.subjects(RDF.type, PL.DyadEvidence))
    n_total = len(dyad_evidences)
    n_complete = 0

    for dev in dyad_evidences:
        derivations = list(g.objects(dev, PL.derivedFrom))
        if len(derivations) == 2:
            n_complete += 1

    completeness = n_complete / n_total if n_total > 0 else 0.0
    return {
        "n_dyad_evidence": n_total,
        "n_complete": n_complete,
        "completeness_rate": round(completeness, 4),
    }


def _score_soundness(g: Graph) -> Dict[str, Any]:
    """Verify dyadScore <= min(comp1, comp2) for all DyadEvidence."""
    dyad_evidences = list(g.subjects(RDF.type, PL.DyadEvidence))
    n_total = 0
    n_sound = 0
    mismatches = []

    for dev in dyad_evidences:
        scores = list(g.objects(dev, PL.score))
        derivations = list(g.objects(dev, PL.derivedFrom))

        if not scores or len(derivations) != 2:
            continue

        dyad_score = float(scores[0])
        comp_scores = []
        for ev in derivations:
            ev_scores = list(g.objects(ev, PL.score))
            if ev_scores:
                comp_scores.append(float(ev_scores[0]))

        if len(comp_scores) == 2:
            n_total += 1
            expected_min = min(comp_scores)
            # Allow small floating-point tolerance
            if dyad_score <= expected_min + 1e-9:
                n_sound += 1
            else:
                mismatches.append({
                    "dyad_evidence": str(dev),
                    "dyad_score": dyad_score,
                    "comp_scores": comp_scores,
                    "expected_min": expected_min,
                })

    soundness = n_sound / n_total if n_total > 0 else 0.0
    return {
        "n_checked": n_total,
        "n_sound": n_sound,
        "soundness_rate": round(soundness, 4),
        "n_mismatches": len(mismatches),
        "mismatches_sample": mismatches[:5],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(use_inference: bool = False) -> Path:
    """Run ontology QA pipeline."""
    print("Step 9: Ontology QA (SHACL + Competency Queries)")

    # Check prerequisites
    if not INFERENCE_OUT.exists():
        print(f"  WARNING: {INFERENCE_OUT} not found. Run step 3b first.")
        print("  Attempting with available data...")

    # Load graph
    g = _load_graph()
    print(f"  Total triples: {len(g)}")

    # 1. SHACL validation
    print("\n  --- SHACL Validation ---")
    shacl_results = _run_shacl(g, use_inference=use_inference)
    status = "PASSED" if shacl_results.get("conforms") else "FAILED"
    print(f"  Status: {status}")
    print(f"  Violations: {shacl_results.get('n_violations', '?')}")
    print(f"  Warnings: {shacl_results.get('n_warnings', '?')}")

    # 2. Competency Queries
    print("\n  --- Competency Queries ---")
    cq_results = _run_all_cqs(g)
    for q in cq_results["queries"]:
        mark = "PASS" if q["pass"] else "FAIL"
        print(f"  [{mark}] {q['file']}: {q['n_rows']} rows — {q['description']}")
    print(f"  CQ score: {cq_results['n_pass']}/{cq_results['n_total']}")

    # 3. derivedFrom completeness
    print("\n  --- derivedFrom Completeness ---")
    df_completeness = _derived_from_completeness(g)
    print(f"  {df_completeness['n_complete']}/{df_completeness['n_dyad_evidence']} "
          f"({df_completeness['completeness_rate']:.1%})")

    # 4. Score soundness
    print("\n  --- Score Soundness ---")
    soundness = _score_soundness(g)
    print(f"  {soundness['n_sound']}/{soundness['n_checked']} "
          f"({soundness['soundness_rate']:.1%})")

    # Build output
    output: Dict[str, Any] = {
        "shacl": shacl_results,
        "competency_queries": cq_results,
        "derived_from_completeness": df_completeness,
        "score_soundness": soundness,
        "summary": {
            "shacl_conforms": shacl_results.get("conforms"),
            "violations_per_1k": shacl_results.get("violations_per_1k_triples"),
            "cq_pass_rate": f"{cq_results['n_pass']}/{cq_results['n_total']}",
            "derivedFrom_completeness": df_completeness["completeness_rate"],
            "score_soundness": soundness["soundness_rate"],
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Written to: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ontology QA: SHACL + CQ KPIs")
    parser.add_argument("--inference", action="store_true",
                        help="Enable RDFS inference for SHACL validation")
    args = parser.parse_args()
    main(use_inference=args.inference)
