"""Language detection primitives for the NLP pipeline."""

from backend.core.language.detector import LanguageDetector
from backend.core.language.schemas import DetectedLanguage, LanguageDetectionResult

__all__ = [
    "DetectedLanguage",
    "LanguageDetectionResult",
    "LanguageDetector",
]
