"""Accuracy and reliability harness for AI extraction — runs against the live Anthropic API.

Usage:
    ANTHROPIC_API_KEY=... ./venv/bin/python eval_ai_extraction.py [--cases id1,id2]

Runs every golden case in tests/fixtures/ai_extraction_cases.json through
app.services.ai.extraction.extract_client_data and scores the result:

    recall           expected facts the model found with the correct value
    precision        extracted facts that were expected and correct
    hallucinations   extracted fields that are not in the expected set at all
    wrong values     right field, wrong value

Exits non-zero when aggregate precision or recall fall below the thresholds,
so it can gate a release. Not part of the default pytest run — it costs real
API calls.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
FIXTURES = ROOT_DIR / "tests" / "fixtures" / "ai_extraction_cases.json"

PRECISION_THRESHOLD = 0.85
RECALL_THRESHOLD = 0.80


def _values_equal(expected, actual) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected is actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(expected) - float(actual)) < 1e-6
    return expected == actual


def score_case(expected: dict, extracted: dict) -> dict:
    correct = [k for k in extracted if k in expected and _values_equal(expected[k], extracted[k])]
    wrong_value = [k for k in extracted if k in expected and not _values_equal(expected[k], extracted[k])]
    hallucinated = [k for k in extracted if k not in expected]
    missed = [k for k in expected if k not in extracted]

    precision = len(correct) / len(extracted) if extracted else 1.0
    recall = len(correct) / len(expected) if expected else 1.0

    return {
        "correct": correct,
        "wrong_value": wrong_value,
        "hallucinated": hallucinated,
        "missed": missed,
        "precision": precision,
        "recall": recall,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate AI extraction accuracy on the golden cases.")
    parser.add_argument("--cases", help="Comma-separated case ids to run (default: all).")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        print("ANTHROPIC_API_KEY is not set — this harness calls the live Anthropic API.")
        return 2

    from app.config import ai_model
    from app.services.ai.extraction import extract_client_data

    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"]
    if args.cases:
        wanted = {c.strip() for c in args.cases.split(",")}
        cases = [case for case in cases if case["id"] in wanted]
        if not cases:
            print(f"No cases match: {args.cases}")
            return 2

    print(f"Model: {ai_model()} — running {len(cases)} case(s)\n")

    total_correct = total_extracted = total_expected = total_hallucinated = 0
    cache_reads = 0
    failures: list[str] = []

    for case in cases:
        expected = case["expected_client_data"]
        try:
            result = extract_client_data(case["notes"])
        except Exception as exc:  # noqa: BLE001 — report the failure and keep scoring the rest
            failures.append(case["id"])
            print(f"✗ {case['id']}: extraction call failed — {exc}")
            continue

        extracted = result["client_data"]
        scores = score_case(expected, extracted)

        total_correct += len(scores["correct"])
        total_extracted += len(extracted)
        total_expected += len(expected)
        total_hallucinated += len(scores["hallucinated"])
        cache_reads += result["usage"]["cache_read_input_tokens"]

        print(
            f"{'✓' if scores['recall'] >= RECALL_THRESHOLD and scores['precision'] >= PRECISION_THRESHOLD else '•'} "
            f"{case['id']}: precision {scores['precision']:.2f}, recall {scores['recall']:.2f} "
            f"({len(scores['correct'])}/{len(expected)} expected facts)"
        )
        for key in scores["missed"]:
            print(f"    missed       {key} (expected {expected[key]!r})")
        for key in scores["wrong_value"]:
            print(f"    wrong value  {key}: expected {expected[key]!r}, got {extracted[key]!r}")
        for key in scores["hallucinated"]:
            print(f"    hallucinated {key} = {extracted[key]!r}")
        for warning in result["warnings"]:
            print(f"    warning      {warning}")

    if failures:
        print(f"\n{len(failures)} case(s) failed to run: {', '.join(failures)}")
        return 1

    precision = total_correct / total_extracted if total_extracted else 1.0
    recall = total_correct / total_expected if total_expected else 1.0

    print("\n── Aggregate ──────────────────────────────────────")
    print(f"precision        {precision:.3f}  (threshold {PRECISION_THRESHOLD})")
    print(f"recall           {recall:.3f}  (threshold {RECALL_THRESHOLD})")
    print(f"hallucinations   {total_hallucinated} field(s) across {len(cases)} case(s)")
    print(f"cache reads      {cache_reads} tokens served from prompt cache")

    if precision < PRECISION_THRESHOLD or recall < RECALL_THRESHOLD:
        print("\nBelow threshold — investigate the misses above before shipping.")
        return 1
    print("\nAll thresholds met.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
