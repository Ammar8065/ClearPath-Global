# ClearPath Global — Risk Intelligence Platform

Rules-based cross-border risk intelligence for advisory teams. Privacy-first by default: rules and knowledge sources are persisted, but client financial facts are evaluated statelessly and never stored. Generates professional HTML and downloadable PDF assessment reports. Optional AI assist (Anthropic API) extracts worksheet facts from pasted client notes and writes plain-English executive summaries of triggered rules.

---

## Table of Contents

- [Overview](#overview)
- [Stack](#stack)
- [Privacy Model](#privacy-model)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Running the Server](#running-the-server)
- [Database Management](#database-management)
- [Seeding](#seeding)
- [Testing](#testing)
- [API Reference](#api-reference)
- [AI Assist (Anthropic API)](#ai-assist-anthropic-api)
- [Evaluation Payload](#evaluation-payload)
- [Scoring Model](#scoring-model)
- [Rule Conditions](#rule-conditions)
- [Architecture](#architecture)
- [Frontend](#frontend)
- [What Is Not Yet Implemented](#what-is-not-yet-implemented)

---

## Overview

ClearPath Global evaluates a flat dictionary of client facts against a versioned library of compliance rules. Each rule carries a jurisdiction, category, risk level, confidence level, and a structured JSON condition expression. The engine fires rules whose conditions match, computes category and jurisdiction breakdowns, and returns a risk tier and numeric score. Nothing from the client payload is ever written to the database in the default privacy mode.

Supported jurisdictions: Australia (AU), Singapore (SG), Hong Kong (HK), United Arab Emirates (UAE), United States (US).

---

## Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.11+ |
| Web framework | FastAPI 0.118 |
| Server | Uvicorn 0.37 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic 1.14 |
| Validation | Pydantic 2.12 |
| PDF rendering | Playwright 1.59 (Chromium headless) |
| AI assist | Anthropic API (`anthropic` 0.116, structured outputs) |
| Database | SQLite (`risk_intelligence.db` by default) |
| Frontend | Vanilla JavaScript SPA served by FastAPI |

---

## Privacy Model

`PRIVACY_MODE=1` is active by default. Its effects:

- `POST /evaluate/private`, `/evaluate/private/preview`, and `/evaluate/private/report` are the canonical evaluation paths. They accept a flat `client_data` dict, run the evaluation engine in memory, and return results without writing any client data.
- `GET/POST /clients` and `GET/POST /assets` return `HTTP 403`.
- `client_id` in `EvaluationResponse` is always `null`.
- Repeatability is managed via local JSON export/import in the browser.

Setting `PRIVACY_MODE=0` re-enables the `/clients` and `/assets` routes for environments where persistent client records are appropriate.

---

## Prerequisites

- Python 3.11 or later
- A virtual environment at `./venv` (see Setup below)
- Playwright Chromium browser (required for PDF generation only)

---

## Setup

**macOS / Linux:**

```bash
# 1. Create the virtual environment
python3 -m venv venv

# 2. Install Python dependencies
./venv/bin/python -m pip install -r requirements.txt

# 3. Install Playwright's Chromium browser (required for PDF export)
./venv/bin/python -m playwright install chromium

# 4. Apply all database migrations
./venv/bin/python -m alembic upgrade head

# 5. Load the seed knowledge base (sources and rules)
./venv/bin/python seed_data.py
```

**Windows (PowerShell):**

```powershell
# 1. Create and activate the virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install Python dependencies
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Install Playwright's Chromium browser (required for PDF export)
.\venv\Scripts\python.exe -m playwright install chromium

# 4. Apply all database migrations
.\venv\Scripts\python.exe -m alembic upgrade head

# 5. Load the seed knowledge base (sources and rules)
.\venv\Scripts\python.exe seed_data.py
```

After these steps the server is ready to start.

---

## Environment Variables

Variables can be set in the shell or in a `.env` file at the project root — `app/config.py`
loads it automatically at import time (real environment variables always take precedence).

| Variable | Default | Effect |
|----------|---------|--------|
| `PRIVACY_MODE` | `1` | Set to `0` to re-enable `/clients` and `/assets` routes |
| `DATABASE_URL` | `sqlite:///./risk_intelligence.db` | Override the SQLite path or use a different database URL |
| `AUTO_CREATE_SCHEMA` | _(unset)_ | Set to `1` to call `create_all()` at startup as a dev fallback. Alembic migrations are the preferred path. |
| `ANTHROPIC_API_KEY` | _(unset)_ | Enables the AI assist endpoints and UI. When unset, `/ai/*` returns `503` and the AI controls stay hidden — everything else works normally. |
| `AI_MODEL` | `claude-sonnet-4-6` | Override the Claude model used for extraction and summarisation. |
| `CLERK_SECRET_KEY` | _(unset)_ | Enables login (Clerk). When unset the app is open with full access — dev/test mode. When set, every API route requires a signed-in Clerk user. |
| `CLERK_PUBLISHABLE_KEY` | _(unset)_ | Clerk frontend key, served to the browser via `/auth/status`. Required whenever `CLERK_SECRET_KEY` is set. |
| `ADMIN_USER_ID` | _(unset)_ | Clerk user ID (`user_...`) of the single administrator. Only this account can add/delete rules and sources; every other signed-in user is a read-only viewer. |
| `CORS_ALLOW_ORIGINS` | _(unset)_ | Comma-separated origins allowed to call the API cross-origin. Unset (the default) grants no cross-origin access — the SPA is served same-origin and needs none. |

---

## Running the Server

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000` | Browser SPA (private assessment worksheet) |
| `http://127.0.0.1:8000/docs` | Swagger UI |
| `http://127.0.0.1:8000/health` | Health check — returns `{"status": "ok"}` |

---

## Database Management

The database is SQLite at `risk_intelligence.db` by default. Override with `DATABASE_URL`.

**Apply all pending migrations:**
```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
```

**Generate a new migration after model changes:**
```powershell
.\venv\Scripts\python.exe -m alembic revision --autogenerate -m "description"
```

`render_as_batch=True` is set globally in `alembic/env.py` for SQLite ALTER TABLE compatibility.

Current migrations (in order):
1. `125257ea` — initial schema
2. `a3f8c21d` — add `section_reference` to rules
3. `b7e4f12c` — add `review_status` to rules
4. `c1d5f6a7` — add `rule_interactions` table

---

## Seeding

The seed pipeline populates knowledge sources and rules from `seed_sources.py` and `seed_rules.py`. The entry point is `seed_data.py`.

```powershell
# Standard upsert (safe to re-run)
.\venv\Scripts\python.exe seed_data.py

# Wipe existing rules and sources before reseeding
.\venv\Scripts\python.exe seed_data.py --reset

# Drop and recreate all tables, then seed (use after schema changes)
.\venv\Scripts\python.exe seed_data.py --recreate
```

---

## Testing

```powershell
# Run the full suite
.\venv\Scripts\python.exe -m pytest -q

# Run a single test file
.\venv\Scripts\python.exe -m pytest tests/test_evaluator.py -q

# Run a single test by name
.\venv\Scripts\python.exe -m pytest tests/test_evaluator.py -k "test_name" -q
```

**Test suites:**

| File | Covers |
|------|--------|
| `tests/test_evaluator.py` | All engine operators, nested condition groups, scoring, version deduplication, `run_evaluation` end-to-end, citation deduplication, incomplete-rule detection, write-time schema validation |
| `tests/test_http_integration.py` | Live HTTP flow against a temporary migrated database: private evaluation, privacy-mode 403 enforcement, root SPA response |
| `tests/test_regressions.py` | `is_empty`/`not_empty` without value key, soft-deleted client rejection, asset tenant filtering, clean Alembic upgrade table verification, frontend not pinned to localhost |
| `tests/test_ai_extraction.py` | Extraction validation/coercion against the field catalog, prompt construction, refusal handling, `/ai/extract` gating and SDK error mapping, eval-harness scoring, golden fixture integrity (Anthropic client fully stubbed) |
| `tests/test_ai_summary.py` | Summary payload privacy guarantee (no client values leave the machine), `/ai/summarise` flow, PDF report AI-section rendering and graceful fallback |
| `tests/test_ai_field_catalog.py` | Drift guard: Python field catalog stays in lockstep with `frontend/evaluation_config.js` (keys and types) |

---

## API Reference

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves the browser SPA (`index.html`) |
| `GET` | `/health` | Returns `{"status": "ok"}` |

### Knowledge Sources

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sources` | List all knowledge sources |
| `POST` | `/sources` | Create a knowledge source |

**Create source payload:**
```json
{
  "jurisdiction": "AU",
  "title": "ATO — Tax residency guidance for individuals",
  "url": "https://www.ato.gov.au/...",
  "source_type": "government_guidance"
}
```

`source_type` values: `government_guidance`, `legislation`, `guidance`, `treaty`, `commentary`.

### Rules

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rules` | List all active rules (with source) |
| `POST` | `/rules` | Create a rule (returns `HTTP 409` on duplicate `rule_code` + `version`) |
| `DELETE` | `/rules/{rule_id}` | Soft-delete a rule |
| `GET` | `/evaluate/rules/{rule_code}/versions` | Full version history for a rule code |

Rules use `rule_code` + `version` as a unique pair. New versions are inserted as new rows, never in-place updates.

**Create rule payload:**
```json
{
  "rule_code": "AU_RES_001",
  "jurisdiction": "AU",
  "category": "residency",
  "condition_expression": {
    "field": "days_in_country",
    "operator": ">=",
    "value": 183
  },
  "description": "183-day statutory test for Australian tax residency.",
  "risk_level": "high",
  "confidence_level": "high",
  "source_id": 1,
  "version": 1,
  "effective_from": "2025-01-01",
  "effective_to": null
}
```

`category` values: `residency`, `tax`, `cross_border`, `structure`.  
`risk_level` / `confidence_level` values: `low`, `medium`, `high`.  
`review_status` values: `verified_current`, `needs_update`, `unsupported_or_wrong_source`. Defaults to `needs_update` — a newly created rule is unverified until someone fact-checks it (the seeder marks its verified fixtures `verified_current` explicitly).

`condition_expression` is validated structurally at write time by `app/schemas/rule.py` before reaching the database. A malformed expression is rejected with a descriptive error.

### Private Evaluation (canonical paths in privacy mode)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/evaluate/private` | Full stateless evaluation — returns score, breakdown, citations |
| `POST` | `/evaluate/private/preview` | Matched/unmatched per rule with reason — no scoring |
| `POST` | `/evaluate/private/report` | Returns a downloadable PDF assessment report |

### Client Evaluation (blocked in privacy mode)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/evaluate/{client_id}` | Full evaluation against a stored client |
| `POST` | `/evaluate/{client_id}/preview` | Preview rule matching for a stored client |
| `GET` | `/clients` | List clients (403 in privacy mode) |
| `POST` | `/clients` | Create client (403 in privacy mode) |
| `DELETE` | `/clients/{client_id}` | Soft-delete client (403 in privacy mode) |
| `GET` | `/assets` | List assets (403 in privacy mode) |
| `POST` | `/assets` | Create asset (403 in privacy mode) |

---

## AI Assist (Anthropic API)

Optional layer powered by the Anthropic API. Active only when `ANTHROPIC_API_KEY` is set; the frontend checks `GET /ai/status` and hides all AI controls when disabled.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ai/status` | `{"enabled": bool, "model": str}` — drives frontend visibility |
| `POST` | `/ai/extract` | Extract worksheet facts from pasted notes. Body: `{"notes": "..."}` (max 50,000 chars). Returns `client_data`, per-fact evidence quotes, `unmapped_notes`, and validation `warnings`. |
| `POST` | `/ai/summarise` | Turn an `EvaluationResponse` into a plain-English executive summary. Body: `{"evaluation": <EvaluationResponse>}`. Returns headline, overview, key risks, recommended actions, and one explanation per triggered rule. |

`POST /evaluate/private/report` additionally accepts `"include_ai_summary": true` to embed the executive summary as the first section of the PDF. If the AI call fails for any reason the report still renders — a warning is appended instead.

Both features use structured outputs (`client.messages.parse` with Pydantic models), so responses are schema-validated before ClearPath touches them. Every extracted value is then re-validated against the field catalog (`app/services/ai/field_catalog.py`) — unknown fields, wrong types, and invalid enum values are dropped into `warnings`, never into the payload. Extraction follows the engine's incomplete-data philosophy: a fact absent from the notes stays absent; it is never inferred as a "no".

**Privacy model (two tiers):**

- **Extraction** sends the pasted notes to Anthropic's API for the duration of the request. It is an explicit opt-in action, and ClearPath stores neither the notes nor the result.
- **Summarisation** sends *rule outcomes only* — rule codes, descriptions, scores, categories, citations, and the names of missing fields. Raw client financial values and the assessment label are never included (`_summary_payload()` in `app/services/ai/summarisation.py`, enforced by a regression test).

**Error mapping:** Anthropic rate limits surface as `429`, connectivity failures as `503`, upstream API errors as `502`, and refusals/unparseable output as `422`. The SDK's built-in retries (2 attempts with backoff) handle transient failures.

**Accuracy harness** — the milestone's example-case testing lives in two layers:

```powershell
# Mocked unit tests (no API key, part of the default suite)
.\venv\Scripts\python.exe -m pytest tests/test_ai_extraction.py tests/test_ai_summary.py tests/test_ai_field_catalog.py -q

# Live golden-case evaluation against the real API (costs tokens)
$env:ANTHROPIC_API_KEY = "sk-ant-..."
.\venv\Scripts\python.exe eval_ai_extraction.py            # all 10 cases
.\venv\Scripts\python.exe eval_ai_extraction.py --cases au-expat-basics,messy-email
```

The harness scores per-field **precision** (threshold 0.85), **recall** (threshold 0.80), **hallucinated fields**, and **wrong values** against `tests/fixtures/ai_extraction_cases.json`, and exits non-zero below threshold. The fixture set includes a no-facts "hallucination probe" and a negation-vs-absence case to verify the model distinguishes an explicit "no" from missing information.

**Ask ClearPath (RAG search)** — a third AI Assist feature, backed by the vector database described in [RAG Pipeline](#rag-pipeline) below, not by direct database access:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/rag/status` | `{"vector_db_available": bool, "ai_enabled": bool, "rule_count": int, "source_chunk_count": int}` — drives frontend visibility |
| `POST` | `/rag/query` | Body: `{"question": "..."}` (max 2,000 chars). Retrieves the most relevant rules and source excerpts, then asks the model to answer using only that material. Returns `answer`, an optional `caveat` when the retrieved context only partially covers the question, and `citations` (rule/source, title, URL, jurisdiction). |

Every citation is rebuilt server-side from the metadata of what was actually retrieved — a rule_code or source_key the model names but that wasn't retrieved is silently dropped, so a citation can never point at something the model invented (see `_build_citations` in `app/services/rag/answer.py`, and the "drops fabricated citations" regression test in `tests/test_rag.py`). Requires both `ANTHROPIC_API_KEY` and a built vector database (`python rag/build_vector_db.py`); `GET /rag/status` reports which, if either, is missing so the frontend can explain why the panel is unavailable.

Executive summaries (`POST /ai/summarise`) are additionally grounded in this same database: each triggered rule is enriched with a short verbatim excerpt from its own cited source page before the summarisation call, so explanations can quote official guidance instead of only paraphrasing the rule's stored description (`_enrich_with_source_excerpts` in `app/services/ai/summarisation.py`). This is best-effort — summaries generate identically to before if the vector database hasn't been built.

---

## Evaluation Payload

```json
POST /evaluate/private
{
  "assessment_label": "Matter 24-017",
  "jurisdiction_scope": ["AU"],
  "client_data": {
    "days_in_country": 190,
    "citizenship": "US",
    "tax_residency_status": "resident",
    "foreign_source_income": 145000,
    "domicile_country": "AU",
    "permanent_abode_outside_country": false
  }
}
```

`client_data` accepts up to 200 fields. Any field absent from the payload causes rules that require it to be moved to `incomplete_rules` rather than silently evaluating to false. This distinction is critical for advisory confidence.

`jurisdiction_scope` (optional) limits the evaluation to the listed jurisdiction codes; codes are
normalised to uppercase. Generic worksheet fields — `days_in_country`, `tax_residency_status`,
`residency_country` — describe *the relevant country* for the assessment, so scoping prevents
another jurisdiction's rules from reading the same value as its own fact (e.g. an Australian
day count being tested against Hong Kong's 60-day exemption). Omitted or empty means every
active rule is evaluated. The browser worksheet sends its focus jurisdictions here automatically;
for genuinely multi-country matters, prefer one scoped assessment per jurisdiction so day counts
and residency statuses stay unambiguous.

**Response shape (`EvaluationResponse`):**

```json
{
  "client_id": null,
  "assessment_label": "Matter 24-017",
  "overall_risk": "high",
  "score": 74.25,
  "triggered_rules": ["AU_RES_001", "AU_RES_002"],
  "summary": [
    {
      "rule_code": "AU_RES_001",
      "description": "...",
      "risk_level": "high",
      "confidence_level": "high",
      "jurisdiction": "AU",
      "category": "residency",
      "rule_score": 100.0,
      "source_id": 1,
      "source_title": "ATO — Tax residency guidance for individuals",
      "source_url": "https://...",
      "section_reference": "s. 995-1 ITAA 1997 — 183-day test",
      "review_status": "verified_current"
    }
  ],
  "category_breakdown": {
    "residency": { "score": 100.0, "triggered_count": 2, "max_risk": "high" },
    "tax":       { "score": 0.0,   "triggered_count": 0, "max_risk": "low"  },
    "cross_border": { "score": 0.0, "triggered_count": 0, "max_risk": "low" },
    "structure": { "score": 0.0,   "triggered_count": 0, "max_risk": "low"  }
  },
  "jurisdiction_breakdown": {
    "AU": { "score": 100.0, "triggered_count": 2 }
  },
  "citations": [
    {
      "rule_code": "AU_RES_001",
      "source_title": "ATO — Tax residency guidance for individuals",
      "source_url": "https://...",
      "jurisdiction": "AU",
      "section_reference": "s. 995-1 ITAA 1997 — 183-day test"
    }
  ],
  "incomplete_rules": [],
  "warnings": []
}
```

Citations are deduplicated by `(source_url, section_reference)` pair. Two rules from the same source citing different sections produce two citations — critical for legal traceability.

`warnings` contains messages for any rules whose condition expressions were malformed at evaluation time. A bad rule is skipped, never a crash.

---

## Scoring Model

All scoring logic lives in `app/engine/scorer.py` as pure functions with no I/O.

**Rule score (0–100):**
```
rule_score = (risk_weight / 3) × confidence_weight × 100

risk_weight:        low=1, medium=2, high=3
confidence_weight:  low=0.6, medium=0.8, high=1.0
```

Examples:
| Risk | Confidence | Score |
|------|-----------|-------|
| high | high | 100.0 |
| high | medium | 80.0 |
| medium | high | 66.67 |
| low | medium | 26.67 |
| low | low | 20.0 |

**Category score:** average `rule_score` for triggered rules in that category.

**Overall numeric score:** weighted average across all four categories:
```
residency    30%
tax          30%
cross_border 25%
structure    15%
```

**Overall risk tier:** always `max(risk_level)` across triggered rules. A single high-risk trigger cannot be diluted by many low-risk matches. Returns `"low"` when no rules fire.

---

## Rule Conditions

Conditions are stored as structured JSON. Three forms:

**Leaf — single field comparison:**
```json
{ "field": "days_in_country", "operator": ">=", "value": 183 }
```

**AND group:**
```json
{
  "all": [
    { "field": "domicile_country", "operator": "==", "value": "AU" },
    { "field": "permanent_abode_outside_country", "operator": "==", "value": false }
  ]
}
```

**OR group:**
```json
{
  "any": [
    { "field": "citizenship", "operator": "==", "value": "AU" },
    { "field": "tax_residency_status", "operator": "==", "value": "resident" }
  ]
}
```

Groups nest arbitrarily deep. `all` and `any` can contain other `all`/`any` nodes.

**Supported operators:**

| Operator | Behaviour |
|----------|-----------|
| `==`, `!=`, `>`, `>=`, `<`, `<=` | Standard comparison |
| `in` | If actual is list/set: checks `expected in actual`. Else if expected is a list/set: checks `actual in expected`. Otherwise (both scalars): plain equality — strings are never treated as containers, so `"US"` does not match inside `"AUS"`. |
| `not_in` | Negation of `in` |
| `contains` | Case-insensitive substring. `actual` must be a string. |
| `starts_with` | Case-insensitive prefix. `actual` must be a string. |
| `is_empty` | True when actual is `None`, `""`, whitespace-only, `[]`, `{}`, `()`, or when the field is absent from `client_data` entirely. `0` and `False` are not empty. |
| `not_empty` | Negation of `is_empty` |

If a field referenced by a comparison operator is absent from `client_data`, the rule moves to `incomplete_rules` (field listed in `missing_fields`). Fields referenced only by `is_empty`/`not_empty` are not required — those operators are well-defined on missing data: a fact that was never provided is empty, so `is_empty` matches and `not_empty` does not.

---

## Rule Interactions

Rules are evaluated independently, so two rules can both legitimately trigger even when one changes what the other's finding actually means in practice — e.g. a UAE entity can be flagged for the standard 9% Corporate Tax (`UAE_TAX_001`) and, separately, for Small Business Relief eligibility (`UAE_TAX_002`), without either rule knowing the other exists. Left as two independent findings, a report reads as if both apply in full, when in fact electing SBR can zero out the CT liability.

`RuleInteraction` rows (`app/models/rule_interaction.py`, seeded from `seed_rule_interactions.py`) capture curated, source-grounded relationships between specific rule_codes. Two types:

| Type | Meaning |
|------|---------|
| `relief` | The related rule is an election the client can make that reduces or eliminates the primary rule's exposure. |
| `exception` | The related rule's own facts are an automatic carve-out from the primary rule — no election needed. |

After evaluation, `app/engine/interactions.py` checks the curated set against whichever rule_codes actually triggered in *this* assessment and returns only the pairs where both sides fired (`EvaluationResponse.rule_interactions`). A relationship referencing a rule that didn't trigger — or a malformed row — is silently skipped (with a warning for the latter), never raised; interaction resolution can never fail an evaluation. Matching results render as an "Interacting Findings" section in both the PDF report and the frontend assessment view.

Every curated note is written to state only what the two rules' own (already fact-checked) descriptions already say — no new legislative claims are introduced by the relationship layer itself. Add new pairs to `seed_rule_interactions.py`; `seed_data.py` fails loudly at seed time if either rule_code doesn't exist in `RULE_FIXTURES`.

---

## Architecture

### Request Path

```
Browser / Swagger UI
    → FastAPI route (app/routes/)
    → Pydantic schema validation (app/schemas/)
    → Service (app/services/)
    → SQLAlchemy ORM (app/models/) → SQLite

For evaluation specifically:
POST /evaluate/private
    → routes/evaluation.py
    → services/evaluation.py
        → _active_rules()  [DB query + version deduplication]
        → engine.run_evaluation(client, rules, client_data)  [pure, zero DB]
    → EvaluationResponse
```

### Layer Responsibilities

| Layer | Path | Role |
|-------|------|------|
| Routes | `app/routes/` | HTTP boundary only — parse request, delegate to service, return response |
| Services | `app/services/` | Business logic and DB orchestration |
| Engine | `app/engine/` | Pure functions, zero DB dependency, fully unit-testable in isolation |
| Models | `app/models/` | SQLAlchemy ORM entities |
| Schemas | `app/schemas/` | Pydantic request/response contracts. `schemas/rule.py` validates condition expressions at write time. |

### Engine Sub-modules

| Module | Responsibility |
|--------|---------------|
| `app/engine/conditions.py` | Parses and recursively evaluates JSON condition expressions |
| `app/engine/selector.py` | Deduplicates rules — keeps highest `version` per `rule_code` |
| `app/engine/scorer.py` | Rule scores, category/jurisdiction breakdowns, overall score and risk tier |
| `app/engine/report.py` | `run_evaluation()` — composes the above into the final result dict |

### Key Data Invariants

- `rule_code` + `version` is a unique pair. New rule versions are inserts, not updates.
- Rules and clients are soft-deleted via `is_deleted`. Physical deletion is never performed.
- The evaluation engine never raises due to a malformed rule — bad conditions are caught and appended to `warnings`, and evaluation continues for the remaining rules.
- `_active_rules()` in `services/evaluation.py` filters to non-deleted rules whose `effective_from <= today` and `effective_to` is null or `>= today`, then deduplicates by version.

---

## Frontend

Vanilla JavaScript SPA served by FastAPI at `/`. Static files live in `frontend/` and are mounted at `/frontend`.

| File | Role |
|------|------|
| `frontend/core.js` | Shared `API_BASE_URL` (uses `window.location.origin`), constants, DOM element refs, `apiRequest` helper |
| `frontend/navigation.js` | Section switching and sidebar state |
| `frontend/evaluation.js` | Private assessment worksheet: tri-state answers, jurisdiction chips, payload builder |
| `frontend/evaluation_config.js` | Field definitions, groups, presets, focus options for guided assessment |
| `frontend/evaluation_views.js` | Renders `EvaluationResponse` and `PreviewResponse` into DOM |
| `frontend/rules.js` | Rules library CRUD modals and list rendering |
| `frontend/sources.js` | Knowledge sources CRUD modals and list rendering |
| `frontend/dashboard.js` | Dashboard section |

The frontend never hardcodes `localhost:8000` or `127.0.0.1:8000` — all API calls use `window.location.origin` to work regardless of deployment host.

The worksheet's jurisdiction focus (the chips at the top, plus any jurisdiction whose questions
have been answered) is sent as `jurisdiction_scope` with every evaluation, preview, and report
request — only the focused jurisdictions' rules are evaluated. With no focus at all, every
active rule runs (a general review). Only *visible* answered questions enter the payload: if a
follow-up answer's parent question is changed so the follow-up disappears, the stale hidden
answer is dropped rather than silently sent to the engine.

The assessment worksheet supports exporting the current payload as a local JSON file and reimporting it, providing session persistence without storing anything on the server.

---

## RAG Pipeline (rag/)

The `rag/` directory contains a two-step pipeline that scrapes every knowledge-source
page referenced by `seed_sources.py` and builds a persistent vector database for
retrieval-augmented generation.

### 1. Scrape the sources

```bash
venv/bin/python rag/scrape_sources.py
```

- Writes one text file per source to `rag/scraped/{SOURCE_KEY}.txt` (metadata header +
  extracted page text) plus a `manifest.json` with fetch status and timestamps.
- `ato.gov.au` blocks non-Australian traffic (Akamai 403), so ATO pages are fetched from
  the most recent HTTP-200 **Wayback Machine snapshot** of the exact URL — the archived
  copy of the real page, never synthesised content. The snapshot timestamp is recorded in
  the file header and manifest.
- PDF sources (e.g. IRD Hong Kong DIPN/PAM leaflets) are extracted with `pypdf`.
- Thin "hub" landing pages are enriched with the specific sub-pages the rules rely on
  (see `SUPPLEMENTARY_PAGES` in the script), each marked with a `===== SUB-PAGE: url =====`
  separator.

### 2. Build the vector database

```bash
venv/bin/python rag/build_vector_db.py                      # build / rebuild
venv/bin/python rag/build_vector_db.py --query "CGT event I1"  # smoke-test retrieval
```

Creates a persistent **ChromaDB** store at `rag/chroma_db/` (gitignored; rebuild any
time) with two collections:

| Collection | Contents | Metadata |
|-----------|----------|----------|
| `rules` | One document per seeded rule (description + section reference) | rule_code, jurisdiction, category, risk/confidence levels, condition JSON, source key/title/URL |
| `sources` | Scraped pages split into ~1,200-char overlapping chunks | source_key, title, URL, jurisdiction, chunk index |

Embeddings use ChromaDB's default `all-MiniLM-L6-v2` (ONNX, downloaded on first run).
Every retrieved chunk is traceable to the official page it came from via its `url`
metadata, which keeps downstream RAG answers grounded in the scraped sources.

### Source integrity

All 60 sources and 98 rules were verified against the live pages (July 2026): dead or
restructured URLs were replaced with their current official equivalents, rules whose
claims could not be located on any accessible official page were corrected or removed,
and every rule's `review_status` reflects that verification. Two former rules
(`HK_RES_001`, `UAE_TAX_005`) were removed as unverifiable — see the dated notes in
`seed_rules.py`.

---

## What Is Not Yet Implemented

- Authentication and authorisation
- Persistent evaluation result storage
- Background processing for long-running rule sets
- AI extraction from uploaded documents (PDF/DOCX) — currently paste-text only
