#!/usr/bin/env python3
"""
SHACL Validation Script

Validates RDF data against SHACL shapes for the EFO-PlutchikDyad module.
Reference: EFO-PlutchikDyad paper, Appendix E

Usage:
    python scripts/validate_shacl.py [--data DATA_FILE] [--shapes SHAPES_FILE]
"""

import argparse
import sys
from pathlib import Path

try:
    from pyshacl import validate
except ImportError:
    print("Error: pyshacl is required. Install with: pip install pyshacl")
    sys.exit(1)

from rdflib import Graph, Namespace

# Namespaces
PL = Namespace("http://example.org/efo/plutchik#")
FSCHEMA = Namespace("https://w3id.org/framester/schema/")


def load_data_graph(base_dir: Path, data_file: str = None) -> Graph:
    """Load data graph with ontology and instance data."""
    g = Graph()
    g.bind("pl", PL)
    g.bind("fschema", FSCHEMA)

    # Load ontology module
    ontology_path = base_dir / "modules" / "EFO-PlutchikDyad.ttl"
    if ontology_path.exists():
        print(f"Loading ontology: {ontology_path}")
        g.parse(ontology_path, format="turtle")

    # Load data
    if data_file:
        data_path = Path(data_file)
        if not data_path.is_absolute():
            data_path = base_dir / data_file
    else:
        data_path = base_dir / "data" / "sample.ttl"

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    print(f"Loading data: {data_path}")
    g.parse(data_path, format="turtle")

    # Also load inference output if available
    inferred_path = base_dir / "output" / "out.ttl"
    if inferred_path.exists():
        print(f"Loading inferred data: {inferred_path}")
        g.parse(inferred_path, format="turtle")

    print(f"Total triples in data graph: {len(g)}")
    return g


def load_shapes_graph(base_dir: Path, shapes_file: str = None) -> Graph:
    """Load SHACL shapes graph."""
    sg = Graph()

    if shapes_file:
        shapes_path = Path(shapes_file)
        if not shapes_path.is_absolute():
            shapes_path = base_dir / shapes_file
    else:
        shapes_path = base_dir / "shacl" / "plutchik-dyad-shapes.ttl"

    if not shapes_path.exists():
        raise FileNotFoundError(f"Shapes file not found: {shapes_path}")

    print(f"Loading shapes: {shapes_path}")
    sg.parse(shapes_path, format="turtle")
    print(f"Total triples in shapes graph: {len(sg)}")

    return sg


def run_validation(data_graph: Graph, shapes_graph: Graph, inference: bool = False) -> tuple:
    """
    Run SHACL validation.

    Returns:
        (conforms, results_graph, results_text)
    """
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs" if inference else "none",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False,
    )

    return conforms, results_graph, results_text


def print_results(conforms: bool, results_text: str) -> None:
    """Print validation results."""
    print("\n" + "=" * 70)
    print("SHACL Validation Results")
    print("=" * 70)

    if conforms:
        print("\nValidation: PASSED")
        print("All data conforms to SHACL shapes.")
    else:
        print("\nValidation: FAILED")
        print("Some violations were found.")

    print("\n" + "-" * 70)
    print("Detailed Results:")
    print("-" * 70)
    print(results_text)


def main():
    parser = argparse.ArgumentParser(description="SHACL Validation for EFO-PlutchikDyad")
    parser.add_argument("--data", type=str, help="Path to data file")
    parser.add_argument("--shapes", type=str, help="Path to SHACL shapes file")
    parser.add_argument("--inference", action="store_true", help="Enable RDFS inference")
    parser.add_argument("--output", type=str, help="Output validation report to file")
    args = parser.parse_args()

    # Determine base directory
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    print("SHACL Validation for EFO-PlutchikDyad")
    print(f"Reference: EFO-PlutchikDyad paper, Appendix E")
    print("-" * 50)

    try:
        # Load graphs
        data_graph = load_data_graph(base_dir, args.data)
        shapes_graph = load_shapes_graph(base_dir, args.shapes)

        # Run validation
        conforms, results_graph, results_text = run_validation(
            data_graph, shapes_graph, args.inference
        )

        # Print results
        print_results(conforms, results_text)

        # Export if requested
        if args.output:
            output_path = Path(args.output)
            if not output_path.is_absolute():
                output_path = base_dir / args.output
            results_graph.serialize(destination=str(output_path), format="turtle")
            print(f"\nValidation report exported to: {output_path}")

        # Exit with appropriate code
        sys.exit(0 if conforms else 1)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
