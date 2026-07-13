"""AI-assisted extraction of structured client facts from unstructured notes.

Privacy: the pasted notes are sent to the Anthropic API for the duration of the
request and are never persisted by ClearPath. Extraction mirrors the engine's
incomplete-data philosophy — a fact absent from the notes stays absent from the
payload; it is never inferred as a "no".
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.config import ai_model
from app.services.ai.client import AIResponseError, get_client
from app.services.ai.field_catalog import FIELD_CATALOG, catalog_prompt_lines, coerce_value


class ExtractedFact(BaseModel):
    field: str
    value: bool | float | str
    evidence: str


class ExtractionOutput(BaseModel):
    facts: list[ExtractedFact]
    unmapped_notes: list[str]


_SYSTEM_PROMPT = f"""You are a data-extraction assistant for ClearPath Global, a cross-border tax \
risk platform used by professional advisors. You convert an advisor's unstructured client notes \
into structured facts matching a fixed field catalog.

Rules:
- Extract ONLY facts explicitly stated in the notes. Never infer, guess, or generalise.
- A fact that is not mentioned must be omitted entirely — absence of information is NOT "no". \
Only produce a false value when the notes explicitly state the negative.
- Use only field keys from the catalog below, with the exact value type listed.
- Numbers must be plain numerics (no currency symbols, commas, or units). Convert shorthand like \
"$1.2m" to 1200000. Do not convert between currencies.
- For each fact, quote the shortest verbatim snippet of the notes that supports it as evidence.
- Facts in the notes that carry tax-relevance but match no catalog field go in unmapped_notes as \
short paraphrases, so the advisor can capture them manually.
- If the notes contain no extractable facts, return empty lists.

Field catalog:
{catalog_prompt_lines()}"""


def _validate_output(output: ExtractionOutput) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    client_data: dict[str, Any] = {}
    facts: list[dict[str, Any]] = []
    warnings: list[str] = []

    for fact in output.facts:
        spec = FIELD_CATALOG.get(fact.field)
        if spec is None:
            warnings.append(f"Ignored unknown field '{fact.field}'.")
            continue
        if fact.field in client_data:
            warnings.append(f"Ignored duplicate value for '{fact.field}' — kept the first.")
            continue
        value, error = coerce_value(spec, fact.value)
        if error is not None:
            warnings.append(f"Ignored '{fact.field}': {error}.")
            continue
        client_data[fact.field] = value
        facts.append(
            {
                "field": fact.field,
                "label": spec.label,
                "value": value,
                "evidence": fact.evidence,
            }
        )

    return client_data, facts, warnings


def extract_client_data(notes: str) -> dict[str, Any]:
    """Run one stateless extraction call and validate the result against the catalog."""
    response = get_client().messages.parse(
        model=ai_model(),
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"<client_notes>\n{notes}\n</client_notes>\n\nExtract the structured facts.",
            }
        ],
        output_format=ExtractionOutput,
    )

    if response.stop_reason == "refusal":
        raise AIResponseError("The model declined to process these notes.")

    parsed = response.parsed_output
    if parsed is None:
        raise AIResponseError("The model did not return valid structured output.")

    client_data, facts, warnings = _validate_output(parsed)
    return {
        "client_data": client_data,
        "facts": facts,
        "unmapped_notes": parsed.unmapped_notes,
        "warnings": warnings,
        "model": response.model,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_creation_input_tokens": response.usage.cache_creation_input_tokens,
            "cache_read_input_tokens": response.usage.cache_read_input_tokens,
        },
    }
