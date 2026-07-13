"""Grounded question-answering over the rules/sources vector database.

Retrieval (app.services.rag.retrieval) finds candidate rules and source
excerpts; this module asks the model to answer using ONLY that material and
to name what it relied on. Citations returned to the caller are then rebuilt
from the retrieved metadata itself — a rule_code or source_key the model
names but that was not actually retrieved is silently dropped, so a citation
can never point somewhere the model made up. This mirrors the field-catalog
validation used for AI extraction.
"""
from __future__ import annotations

from pydantic import BaseModel

from app.config import ai_model
from app.services.ai.client import AIResponseError, get_client
from app.services.rag.retrieval import retrieve_context

_SYSTEM_PROMPT = """You are a research assistant for ClearPath Global, answering questions about \
cross-border tax and residency rules using ONLY the rule and source excerpts provided in <context>. \
You are not the rules engine and are not evaluating a specific client's facts — you are explaining \
what the knowledge base says.

Rules:
- Answer ONLY using the excerpts in <context>. Never invent legislation, rates, thresholds, dates, \
or citations that are not present in the excerpts.
- If the excerpts do not cover the question, or only partially cover it, say so plainly in the answer \
and use the caveat field to state what's missing. Do not guess or fill gaps with general knowledge.
- List every rule_code and source_key you actually relied on in cited_rule_codes / cited_source_keys, \
using the exact identifiers shown in the <context> tags. Do not cite anything you did not use.
- Keep the answer concise and precise — a professional cross-border tax/immigration advisor is \
reading this, not a layperson.
- This is decision support drawn from a rules library, not tax or legal advice.
- Use British English."""


class RAGModelOutput(BaseModel):
    answer: str
    cited_rule_codes: list[str]
    cited_source_keys: list[str]
    caveat: str | None = None


def _context_block(context: dict) -> str:
    parts = []
    for r in context["rules"]:
        parts.append(
            f'<rule rule_code="{r["rule_code"]}" jurisdiction="{r["jurisdiction"]}" '
            f'category="{r["category"]}">\n{r["document"]}\n</rule>'
        )
    for c in context["chunks"]:
        parts.append(
            f'<source source_key="{c["source_key"]}" title="{c["title"]}" '
            f'jurisdiction="{c["jurisdiction"]}">\n{c["document"]}\n</source>'
        )
    return "\n\n".join(parts)


def _build_citations(parsed: RAGModelOutput, context: dict) -> list[dict[str, str]]:
    rule_lookup = {r["rule_code"]: r for r in context["rules"]}
    source_lookup: dict[str, dict] = {}
    for c in context["chunks"]:
        source_lookup.setdefault(c["source_key"], c)

    citations: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for code in parsed.cited_rule_codes:
        r = rule_lookup.get(code)
        if r is None or ("rule", code) in seen:
            continue
        seen.add(("rule", code))
        citations.append({
            "type": "rule",
            "key": code,
            "title": f"{code} — {r.get('section_reference') or r['jurisdiction']}",
            "url": r["source_url"],
            "jurisdiction": r["jurisdiction"],
        })

    for key in parsed.cited_source_keys:
        c = source_lookup.get(key)
        if c is None or ("source", key) in seen:
            continue
        seen.add(("source", key))
        citations.append({
            "type": "source",
            "key": key,
            "title": c["title"],
            "url": c["url"],
            "jurisdiction": c["jurisdiction"],
        })

    return citations


def answer_question(question: str) -> dict:
    """Retrieve context and run one stateless grounded-QA call over it."""
    context = retrieve_context(question)

    response = get_client().messages.parse(
        model=ai_model(),
        max_tokens=8000,
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
                    f"<context>\n{_context_block(context)}\n</context>\n\n"
                    f"<question>\n{question}\n</question>"
                ),
            }
        ],
        output_format=RAGModelOutput,
    )

    if response.stop_reason == "refusal":
        raise AIResponseError("The model declined to answer this question.")

    parsed = response.parsed_output
    if parsed is None:
        raise AIResponseError("The model did not return valid structured output.")

    return {
        "answer": parsed.answer,
        "caveat": parsed.caveat,
        "citations": _build_citations(parsed, context),
        "model": response.model,
    }
