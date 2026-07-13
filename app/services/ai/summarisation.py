"""AI summarisation of a completed evaluation into plain-English explanations.

Privacy: only rule outcomes leave the machine — rule codes, descriptions,
scores, categories, jurisdictions, citations, curated rule-interaction notes,
and the *names* of missing fields. Raw client facts and the assessment label
are never included; see ``_summary_payload`` and its regression test in
tests/test_ai_summary.py.

Grounding: when the rules/sources vector database is available, each
triggered rule is enriched with a short verbatim excerpt from its own cited
source page (``_enrich_with_source_excerpts``), so explanations can quote the
official guidance instead of only paraphrasing the rule's stored
description. This is best-effort — summarisation must keep working exactly
as before when the vector DB hasn't been built.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from app.config import ai_model
from app.services.ai.client import AIResponseError, get_client
from app.services.rag.retrieval import retrieve_excerpt_for_source


class RuleExplanation(BaseModel):
    rule_code: str
    explanation: str


class AISummary(BaseModel):
    headline: str
    overview: str
    key_risks: list[str]
    recommended_actions: list[str]
    rule_explanations: list[RuleExplanation]


_SYSTEM_PROMPT = """You are a senior cross-border tax risk analyst at ClearPath Global writing \
for professional tax and immigration advisors. You receive the machine output of a rules-based \
risk assessment and turn it into a clear narrative the advisor can share with their team.

Rules:
- This is decision support, not tax or legal advice — write accordingly, without hedging every \
sentence.
- Write about THIS client, not about tax law in general. Anchor every sentence in the specific \
rules that fired and how they combine, using the concrete circumstances and thresholds those \
rules evidence (e.g. a day count below a rule's threshold, a retained property, an outstanding \
study loan). If a sentence would read equally true for any client, cut it.
- Explain each triggered rule in plain English: what fired, why it matters, and what it exposes \
the client to. Do not restate the rule description verbatim.
- Where a triggered rule includes a source_excerpt, it is verbatim text from the official page \
that rule cites — prefer grounding the explanation in that wording over paraphrasing the rule \
description alone. Absence of a source_excerpt is not a signal of lower confidence; just explain \
from the rule description as usual.
- rule_interactions describe how two triggered findings modify each other — a relief the client \
can elect, or an exception that automatically carves them out. Weave these connections into the \
overview and recommended_actions instead of presenting the two findings as unrelated.
- Reference ONLY the rules, sources, and section references provided. Never invent legislation, \
case law, thresholds, or figures that are not in the input.
- Treat incomplete_rules as open questions: the facts were missing, so the risk is unassessed — \
not absent. Fold the most important gaps into recommended_actions.
- headline: one sentence stating this client's overall position. overview: structured strictly \
in this order — (1) the core problem in one or two sentences, (2) the principal risks that flow \
from it, (3) a closing sentence on what remains unassessed because facts are missing. Do not \
interleave the three.
- key_risks and recommended_actions: concise, concrete bullet points ordered by severity.
- Provide one rule_explanation per triggered rule, keyed by its rule_code.
- Use British English."""


def _summary_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Reduce an evaluation result to rule outcomes only.

    Deliberately excludes the assessment label and anything else that could
    carry client-identifying or client-financial data. Field *names* in
    missing_fields are part of the rule library, not client data. Pure and
    fast — no vector DB lookups here; see ``_enrich_with_source_excerpts``
    for the grounding step applied only in ``summarise_evaluation``.
    """
    return {
        "overall_risk": result.get("overall_risk"),
        "score": result.get("score"),
        "category_breakdown": result.get("category_breakdown", {}),
        "jurisdiction_breakdown": result.get("jurisdiction_breakdown", {}),
        "triggered_rules": [
            {
                "rule_code": item.get("rule_code"),
                "description": item.get("description"),
                "risk_level": item.get("risk_level"),
                "confidence_level": item.get("confidence_level"),
                "jurisdiction": item.get("jurisdiction"),
                "category": item.get("category"),
                "rule_score": item.get("rule_score"),
                "source_title": item.get("source_title"),
                "source_url": item.get("source_url"),
                "section_reference": item.get("section_reference"),
            }
            for item in result.get("summary", [])
        ],
        "incomplete_rules": [
            {
                "rule_code": item.get("rule_code"),
                "description": item.get("description"),
                "risk_level": item.get("risk_level"),
                "jurisdiction": item.get("jurisdiction"),
                "category": item.get("category"),
                "missing_fields": item.get("missing_fields", []),
            }
            for item in result.get("incomplete_rules", [])
        ],
        # Curated rule-library metadata (see seed_rule_interactions.py) — no client data.
        "rule_interactions": [
            {
                "primary_rule_code": item.get("primary_rule_code"),
                "related_rule_code": item.get("related_rule_code"),
                "interaction_type": item.get("interaction_type"),
                "note": item.get("note"),
            }
            for item in result.get("rule_interactions", [])
        ],
    }


def _enrich_with_source_excerpts(payload: dict[str, Any]) -> dict[str, Any]:
    """Best-effort: attach a verbatim excerpt from each triggered rule's own
    cited source page, so the model can quote official guidance instead of
    only paraphrasing the rule's stored description.

    Queries the vector DB (if built) using the rule's description as the
    search query, restricted to chunks of that rule's own source_url, so the
    excerpt returned is the passage most relevant to *this* rule rather than
    just the top of the page. Silently no-ops per-rule on any failure —
    grounding is an enhancement, never a requirement for summarisation to
    proceed.
    """
    for rule in payload.get("triggered_rules", []):
        source_url = rule.pop("source_url", None)
        description = rule.get("description")
        if not source_url or not description:
            continue
        try:
            chunks = retrieve_excerpt_for_source(description, source_url, n=1)
        except Exception:
            continue
        if chunks:
            rule["source_excerpt"] = chunks[0]["document"][:800]
    return payload


def summarise_evaluation(result: dict[str, Any]) -> dict[str, Any]:
    """Run one stateless summarisation call over the rule outcomes of a result."""
    payload = _enrich_with_source_excerpts(_summary_payload(result))

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
                "content": (
                    "<assessment_result>\n"
                    + json.dumps(payload, indent=2, sort_keys=True)
                    + "\n</assessment_result>\n\nWrite the summary."
                ),
            }
        ],
        output_format=AISummary,
    )

    if response.stop_reason == "refusal":
        raise AIResponseError("The model declined to summarise this assessment.")

    parsed = response.parsed_output
    if parsed is None:
        raise AIResponseError("The model did not return valid structured output.")

    return {"summary": parsed.model_dump(), "model": response.model}
