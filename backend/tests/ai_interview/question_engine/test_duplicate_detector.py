"""
Tests for DuplicateDetector.

Verifies:
  A. Exact duplicate is caught
  B. Case-insensitive duplicate is caught
  C. Whitespace-normalised duplicate is caught
  D. Punctuation-normalised duplicate is caught
  E. Distinct questions are allowed
  F. Empty history is allowed
  G. normalize() helper produces expected output
"""
import pytest

from app.ai_interview.question_engine.duplicate_detector import DuplicateDetector
from app.ai_interview.question_engine.exceptions import DuplicateQuestionError
from tests.ai_interview.question_engine.conftest import make_question_record


# ── G. normalize() helper ────────────────────────────────────────────────────

@pytest.mark.parametrize("raw, expected", [
    ("What is Python?", "what is python"),
    ("  What  IS  Python?  ", "what is python"),
    ("What is Python???", "what is python"),
    ("WHAT IS PYTHON", "what is python"),
    ("What is Python!?!", "what is python"),
    ("What...is...Python", "whatispython"),  # dots removed, no spaces between words without spaces
    ("  ", ""),
])
def test_normalize(raw, expected):
    assert DuplicateDetector.normalize(raw) == expected


# ── F. Empty history ──────────────────────────────────────────────────────────

def test_no_duplicate_with_empty_history():
    # Should not raise
    DuplicateDetector.check("What is Python?", [])


# ── A. Exact duplicate ────────────────────────────────────────────────────────

def test_exact_duplicate_raises():
    history = [make_question_record(question_text="What is Python?")]
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("What is Python?", history)


# ── B. Case-insensitive ───────────────────────────────────────────────────────

def test_case_insensitive_duplicate_raises():
    history = [make_question_record(question_text="What is Python?")]
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("what is python?", history)


def test_all_caps_duplicate_raises():
    history = [make_question_record(question_text="What is Python?")]
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("WHAT IS PYTHON?", history)


# ── C. Whitespace normalisation ───────────────────────────────────────────────

def test_extra_whitespace_duplicate_raises():
    history = [make_question_record(question_text="What is Python?")]
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("  What   is   Python?  ", history)


# ── D. Punctuation normalisation ─────────────────────────────────────────────

def test_punctuation_variant_duplicate_raises():
    history = [make_question_record(question_text="What is Python?")]
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("What is Python", history)  # no question mark


def test_extra_punctuation_duplicate_raises():
    history = [make_question_record(question_text="What is Python?")]
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("What is Python!!!???", history)


# ── E. Distinct questions ─────────────────────────────────────────────────────

def test_distinct_question_allowed():
    history = [make_question_record(question_text="What is Python?")]
    # Should not raise
    DuplicateDetector.check("Explain Python decorators and their use cases.", history)


def test_multiple_history_one_duplicate():
    history = [
        make_question_record(turn_number=1, question_text="What is Python?"),
        make_question_record(turn_number=2, question_text="Explain list comprehension."),
        make_question_record(turn_number=3, question_text="What are decorators?"),
    ]
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("Explain LIST COMPREHENSION.", history)


def test_multiple_history_no_duplicate():
    history = [
        make_question_record(turn_number=1, question_text="What is Python?"),
        make_question_record(turn_number=2, question_text="Explain list comprehension."),
    ]
    # Entirely new question — should not raise
    DuplicateDetector.check("How does Python handle memory management?", history)


# ── Determinism ───────────────────────────────────────────────────────────────

def test_duplicate_detection_is_deterministic():
    history = [make_question_record(question_text="What is Python?")]
    # Same call twice — same result
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("What is Python?", history)
    with pytest.raises(DuplicateQuestionError):
        DuplicateDetector.check("What is Python?", history)
