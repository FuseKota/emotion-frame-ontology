"""
NRC EmoLex-based mapping from GoEmotions 28 labels to Plutchik 8 emotions.

The NRC Word-Emotion Association Lexicon (EmoLex) assigns binary associations
between ~14K English words and Plutchik's 8 basic emotions plus
positive/negative sentiment.

This module provides a static mapping derived from NRC EmoLex that links each
GoEmotions label word to its Plutchik associations.  Because the NRC lexicon
is not redistributable under its licence, we hard-code the relevant rows here
(the 28 GoEmotions label words only) rather than shipping the full file.

Source: Saif Mohammad and Peter Turney.  "Crowdsourcing a Word-Emotion
Association Lexicon."  Computational Intelligence, 29(3), 2013.
"""

from typing import Dict, List

# NRC EmoLex associations for the 28 GoEmotions label words.
# Each key is a GoEmotions label; the value lists the Plutchik emotions
# with which NRC EmoLex marks that word as associated (=1).
#
# Words not present in NRC EmoLex have an empty list.
# "neutral" maps to nothing by definition.

NRC_GOEMOTION_MAP: Dict[str, List[str]] = {
    "admiration": ["Joy", "Trust"],
    "amusement": ["Joy"],
    "anger": ["Anger"],
    "annoyance": ["Anger"],
    "approval": ["Joy", "Trust"],
    "caring": ["Joy", "Trust"],
    "confusion": ["Surprise"],
    "curiosity": ["Anticipation", "Trust"],
    "desire": ["Anticipation", "Joy"],
    "disappointment": ["Sadness", "Surprise"],
    "disapproval": ["Anger", "Sadness"],
    "disgust": ["Anger", "Disgust"],
    "embarrassment": ["Fear", "Sadness"],
    "excitement": ["Anticipation", "Joy", "Surprise"],
    "fear": ["Fear"],
    "gratitude": ["Joy", "Trust"],
    "grief": ["Sadness"],
    "joy": ["Joy"],
    "love": ["Joy", "Trust"],
    "nervousness": ["Anticipation", "Fear"],
    "neutral": [],
    "optimism": ["Anticipation", "Joy", "Trust"],
    "pride": ["Joy"],
    "realization": ["Anticipation", "Surprise"],
    "relief": ["Joy"],
    "remorse": ["Disgust", "Sadness"],
    "sadness": ["Sadness"],
    "surprise": ["Surprise"],
}


def get_nrc_mapping() -> Dict[str, List[str]]:
    """Return the NRC-based GoEmotions → Plutchik mapping."""
    return NRC_GOEMOTION_MAP
