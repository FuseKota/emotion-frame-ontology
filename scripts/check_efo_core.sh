#!/usr/bin/env bash
# check_efo_core.sh — Verify that EFO core (read-only) files have not been modified.
#
# Usage:
#   bash scripts/check_efo_core.sh          # from repo root
#   git hooks: add to .git/hooks/pre-commit
#
# Exit codes:
#   0 = all checksums match (files unchanged)
#   1 = at least one file was modified

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# SHA-256 checksums of the read-only EFO core files
declare -A EXPECTED=(
    ["data/EmoCore_iswc.ttl"]="bca422aa20879d9007fec5474829af6b77cccac2f77d760632b47bf15da47eb9"
    ["data/BE_iswc.ttl"]="374ced1e27747211d59e5e5db6d71b8a6dea5ebc0b45689b3599bd99bd1f7f73"
    ["data/BasicEmotionTriggers_iswc.ttl"]="d10c0057a310288140c5de480457368c1b574dcf2d2ab2b7e0f5c888fbc0c291"
    ["imports/DUL.owl"]="e5f6429596d2c7014730bad85aaaa9c39530235f27f596cd0e7ce85e6bbcba66"
)

failed=0

for rel_path in "${!EXPECTED[@]}"; do
    full_path="$REPO_ROOT/$rel_path"
    expected="${EXPECTED[$rel_path]}"

    if [[ ! -f "$full_path" ]]; then
        echo "MISSING: $rel_path"
        failed=1
        continue
    fi

    # macOS uses shasum, Linux uses sha256sum
    if command -v sha256sum &>/dev/null; then
        actual=$(sha256sum "$full_path" | awk '{print $1}')
    else
        actual=$(shasum -a 256 "$full_path" | awk '{print $1}')
    fi

    if [[ "$actual" != "$expected" ]]; then
        echo "MODIFIED: $rel_path"
        echo "  expected: $expected"
        echo "  actual:   $actual"
        failed=1
    fi
done

if [[ $failed -eq 0 ]]; then
    echo "EFO core integrity check: PASSED (all 4 files unchanged)"
    exit 0
else
    echo ""
    echo "ERROR: EFO core files have been modified!"
    echo "These files are READ-ONLY (De Giorgis & Gangemi 2024 / DOLCE-Ultralite)."
    echo "Please revert any changes to the files listed above."
    exit 1
fi
