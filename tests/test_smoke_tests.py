"""Pure-function unit tests for the bundled runner.

No network. Covers extract_text (both shapes), check_assertions (all three
matcher types + smart-quote folding), and _ascii_fold.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import from scripts/ without installing the package.
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

# ruff: noqa: E402 - path insertion required before import
import importlib.util

_SPEC = importlib.util.spec_from_file_location("smoke_tests", _ROOT / "scripts" / "smoke-tests.py")
assert _SPEC is not None and _SPEC.loader is not None
smoke_tests = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(smoke_tests)

extract_text = smoke_tests.extract_text
check_assertions = smoke_tests.check_assertions
_ascii_fold = smoke_tests._ascii_fold


# ---- _ascii_fold ---------------------------------------------------------


def test_ascii_fold_smart_quotes():
    assert _ascii_fold("don\u2019t") == "don't"
    assert _ascii_fold("\u201chello\u201d") == '"hello"'


def test_ascii_fold_leaves_plain_text_alone():
    assert _ascii_fold("hello world") == "hello world"


# ---- extract_text --------------------------------------------------------


def test_extract_text_prefers_output_text_when_populated():
    payload = {
        "output_text": "hello",
        "output": [{"content": [{"text": "ignored"}]}],
    }
    assert extract_text(payload) == "hello"


def test_extract_text_falls_back_to_structured_when_output_text_empty():
    payload = {
        "output_text": "",
        "output": [{"content": [{"text": "from-structured"}]}],
    }
    assert extract_text(payload) == "from-structured"


def test_extract_text_handles_nested_text_dict():
    payload = {
        "output": [{"content": [{"text": {"value": "nested"}}]}],
    }
    assert extract_text(payload) == "nested"


def test_extract_text_joins_multiple_content_blocks():
    payload = {
        "output": [
            {"content": [{"text": "one"}, {"text": "two"}]},
            {"content": [{"text": "three"}]},
        ],
    }
    assert extract_text(payload) == "one\ntwo\nthree"


def test_extract_text_returns_empty_on_missing_shapes():
    assert extract_text({}) == ""
    assert extract_text({"output": []}) == ""


# ---- check_assertions ----------------------------------------------------


def test_check_assertions_empty_when_all_pass():
    text = "The Autobots defeated Megatron."
    failures = check_assertions(text, {
        "contains_any": ["megatron", "starscream"],
        "contains_all": ["autobots"],
        "contains_none": ["allspark"],
    })
    assert failures == []


def test_check_assertions_flags_contains_any_when_none_match():
    failures = check_assertions("hello world", {"contains_any": ["foo", "bar"]})
    assert len(failures) == 1
    assert "contains_any" in failures[0]


def test_check_assertions_flags_missing_contains_all():
    failures = check_assertions("hello world", {"contains_all": ["hello", "missing"]})
    assert len(failures) == 1
    assert "missing" in failures[0]


def test_check_assertions_flags_forbidden_contains_none():
    failures = check_assertions("paris is nice", {"contains_none": ["paris"]})
    assert len(failures) == 1
    assert "paris" in failures[0]


def test_check_assertions_case_insensitive():
    failures = check_assertions("MEGATRON", {"contains_any": ["megatron"]})
    assert failures == []


def test_check_assertions_folds_smart_quotes_before_match():
    text = "we don\u2019t know"
    failures = check_assertions(text, {"contains_any": ["don't"]})
    assert failures == []


def test_check_assertions_skips_missing_keys():
    failures = check_assertions("anything", {})
    assert failures == []


def test_check_assertions_returns_all_failures_at_once():
    failures = check_assertions("hello", {
        "contains_any": ["foo"],
        "contains_all": ["bar"],
        "contains_none": ["hello"],
    })
    assert len(failures) == 3
