"""
Shared constants for the GoEmotions experiment pipeline.

Centralises dyad definitions, label lists, thresholds, and namespace URIs
that were previously duplicated across scripts.
"""

from pathlib import Path
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Project paths (relative to repository root)
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data" / "experiment"
OUTPUT_DIR = ROOT_DIR / "output" / "experiment"

# ---------------------------------------------------------------------------
# Plutchik 8 basic emotions (canonical order)
# ---------------------------------------------------------------------------
PLUTCHIK_EMOTIONS: List[str] = [
    "Joy",
    "Trust",
    "Fear",
    "Surprise",
    "Sadness",
    "Disgust",
    "Anger",
    "Anticipation",
]

# ---------------------------------------------------------------------------
# Dyad definitions: dyad_name -> (component1, component2)
# Mirrors run_inference.py:29 and threshold_sweep.py:32
# ---------------------------------------------------------------------------
DYADS: Dict[str, Tuple[str, str]] = {
    "Love": ("Joy", "Trust"),
    "Submission": ("Trust", "Fear"),
    "Awe": ("Fear", "Surprise"),
    "Disapproval": ("Surprise", "Sadness"),
    "Remorse": ("Sadness", "Disgust"),
    "Contempt": ("Disgust", "Anger"),
    "Aggressiveness": ("Anger", "Anticipation"),
    "Optimism": ("Anticipation", "Joy"),
    "Hope": ("Anticipation", "Trust"),
    "Pride": ("Anger", "Joy"),
}

DYAD_NAMES: List[str] = list(DYADS.keys())

# ---------------------------------------------------------------------------
# GoEmotions 28 labels (index order from SamLowe/roberta-base-go_emotions)
# ---------------------------------------------------------------------------
GOEMOTION_LABELS: List[str] = [
    "admiration",
    "amusement",
    "anger",
    "annoyance",
    "approval",
    "caring",
    "confusion",
    "curiosity",
    "desire",
    "disappointment",
    "disapproval",
    "disgust",
    "embarrassment",
    "excitement",
    "fear",
    "gratitude",
    "grief",
    "joy",
    "love",
    "nervousness",
    "neutral",
    "optimism",
    "pride",
    "realization",
    "relief",
    "remorse",
    "sadness",
    "surprise",
]

# ---------------------------------------------------------------------------
# Default threshold sweep range
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS: List[float] = [
    round(0.3 + i * 0.05, 2) for i in range(9)   # 0.30 .. 0.70
]

# ---------------------------------------------------------------------------
# RDF namespace URIs
# ---------------------------------------------------------------------------
NS_PL = "http://example.org/efo/plutchik#"
NS_EX = "http://example.org/data#"
NS_FSCHEMA = "https://w3id.org/framester/schema/"
NS_EMO = "http://www.ontologydesignpatterns.org/ont/emotions/EmoCore.owl#"

# ---------------------------------------------------------------------------
# Dyad → relevant SemEval-2018 EI-reg emotion(s) for consistency checks
# (promoted from step4b_semeval_consistency.py)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Focus dyads: sufficient SemEval sample size for robust statistics
# ---------------------------------------------------------------------------
FOCUS_DYADS: List[str] = ["Love", "Disapproval", "Optimism", "Contempt"]

# ---------------------------------------------------------------------------
# Bootstrap / permutation parameters
# ---------------------------------------------------------------------------
N_BOOTSTRAP: int = 2000
N_PERMUTATION: int = 10000
