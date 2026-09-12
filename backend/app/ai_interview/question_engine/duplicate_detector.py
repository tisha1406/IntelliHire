"""
Phase 5 — Question Orchestration & Interview Turn Engine

DuplicateDetector: Deterministic exact-match duplicate detection.

Strategy (Phase 5):
  1. Normalize both the candidate question and each historical question:
       - Strip leading/trailing whitespace
       - Collapse internal whitespace runs to a single space
       - Lowercase the entire string
       - Remove or normalise punctuation (reduce to alphanumeric + spaces)
  2. Compare the normalised candidate against all normalised history entries.
  3. If any match is found → raise DuplicateQuestionError.

This is deliberately conservative and explainable:
  - Same output → same normalised form → deterministic detection.
  - No embeddings, no vector similarity, no thresholds, no LLM judgement.

Future semantic duplicate detection (embeddings / cosine similarity) can be
added as a separate component without touching this class.
"""
import re
from typing import List

from app.ai_interview.question_engine.schemas import QuestionRecord
from app.ai_interview.question_engine.exceptions import DuplicateQuestionError


class DuplicateDetector:
    """
    Deterministic string-normalisation-based duplicate detector.

    Uses only officially dispatched QuestionRecord entries as the comparison
    corpus — rejected or invalid generation attempts are never stored there,
    so they cannot incorrectly block a valid retry.
    """

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalise a question string for duplicate comparison.

        Steps (in order):
          1. Strip leading/trailing whitespace.
          2. Lowercase.
          3. Remove all characters that are not alphanumeric or whitespace.
          4. Collapse multiple whitespace characters into a single space.
          5. Strip again (in case removal left leading/trailing spaces).
        """
        text = text.strip()
        text = text.lower()
        # Remove punctuation (keep only alphanumeric and whitespace)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        # Collapse runs of whitespace to a single space
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def check(candidate_text: str, question_history: List[QuestionRecord]) -> None:
        """
        Check whether candidate_text is a normalised duplicate of any previously
        dispatched question in question_history.

        Args:
            candidate_text:   The generated question text to check.
            question_history: Official dispatched question records from the session.

        Raises:
            DuplicateQuestionError: if a normalised duplicate is detected.
        """
        if not question_history:
            return  # No history — cannot be a duplicate.

        normalised_candidate = DuplicateDetector.normalize(candidate_text)

        for record in question_history:
            normalised_existing = DuplicateDetector.normalize(record.question_text)
            if normalised_candidate == normalised_existing:
                raise DuplicateQuestionError(
                    f"Generated question is a duplicate of a previously dispatched question "
                    f"(turn {record.turn_number}, topic {record.topic_id!r}). "
                    f"Normalised form: {normalised_candidate!r}"
                )
