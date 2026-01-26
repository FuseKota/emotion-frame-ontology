#!/usr/bin/env python3
"""
Extract owl:imports IRIs from TTL/OWL files.
Usage: python extract_imports.py <file.ttl|file.owl>
"""

import sys
import re
from pathlib import Path


def extract_imports_ttl(content: str) -> list[str]:
    """Extract owl:imports from Turtle format."""
    imports = []
    # Pattern: owl:imports <IRI> or owl:imports IRI
    pattern = r'owl:imports\s+<([^>]+)>'
    imports.extend(re.findall(pattern, content))
    return imports


def extract_imports_owl(content: str) -> list[str]:
    """Extract owl:imports from RDF/XML format."""
    imports = []
    # Pattern: <owl:imports rdf:resource="IRI"/>
    pattern = r'<owl:imports\s+rdf:resource="([^"]+)"'
    imports.extend(re.findall(pattern, content))
    return imports


def extract_referenced_iris(content: str) -> list[str]:
    """Extract all external IRIs referenced in the file (not just imports)."""
    iris = set()

    # External HTTP(S) IRIs in angle brackets
    pattern = r'<(https?://[^>]+)>'
    for iri in re.findall(pattern, content):
        # Skip fragment IRIs and keep only base ontology IRIs
        base_iri = iri.split('#')[0]
        iris.add(base_iri)

    return sorted(iris)


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_imports.py <file.ttl|file.owl>")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    content = filepath.read_text(encoding='utf-8')

    print(f"=== Analyzing: {filepath.name} ===\n")

    # Extract explicit owl:imports
    if filepath.suffix == '.owl':
        imports = extract_imports_owl(content)
    else:
        imports = extract_imports_ttl(content)

    print("Explicit owl:imports:")
    if imports:
        for imp in imports:
            print(f"  - {imp}")
    else:
        print("  (none)")

    # Extract all referenced IRIs
    print("\nReferenced external IRIs (base ontologies):")
    refs = extract_referenced_iris(content)
    for ref in refs:
        if 'ontologydesignpatterns.org' in ref or 'w3id.org' in ref or 'dbpedia.org' in ref:
            print(f"  - {ref}")

    print()


if __name__ == "__main__":
    main()
