#!/bin/bash
# EFO Ontology Download Script
# Downloads EmoCore, EFO-BE (BasicEmotions), and dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$BASE_DIR/data"
IMPORTS_DIR="$BASE_DIR/imports"

mkdir -p "$DATA_DIR" "$IMPORTS_DIR"

echo "=== Downloading EFO Ontology Files ==="

# GitHub repository base URL
GITHUB_RAW="https://raw.githubusercontent.com/StenDoipanni/EFO/main"

echo "[1/4] Downloading EmoCore_iswc.ttl..."
curl -sL "$GITHUB_RAW/EmoCore_iswc.ttl" -o "$DATA_DIR/EmoCore_iswc.ttl"

echo "[2/4] Downloading BE_iswc.ttl (EFO-BE: Basic Emotions module)..."
curl -sL "$GITHUB_RAW/BE_iswc.ttl" -o "$DATA_DIR/BE_iswc.ttl"

echo "[3/4] Downloading BasicEmotionTriggers_iswc.ttl (optional)..."
curl -sL "$GITHUB_RAW/BasicEmotionTriggers_iswc.ttl" -o "$DATA_DIR/BasicEmotionTriggers_iswc.ttl"

echo "[4/4] Downloading DUL.owl (DOLCE-Ultralite dependency)..."
curl -sL "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl" -o "$IMPORTS_DIR/DUL.owl"

echo ""
echo "=== Download Complete ==="
echo "Files downloaded:"
ls -la "$DATA_DIR"
ls -la "$IMPORTS_DIR"
