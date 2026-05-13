# ClearPath Global — Architecture

Rules-based cross-border risk intelligence platform. Stores versioned rules and knowledge sources. Evaluates client financial facts statelessly — no persistent client data in default (privacy) mode. Generates professional HTML and PDF assessment reports.

## Milestone State

| Milestone | Status | Scope |
|-----------|--------|-------|
| M1 | Complete | Versioned rules, knowledge source traceability, seed data |
| M2 | Complete | Modular rules engine, numeric scoring, category/jurisdiction breakdown, citations, preview endpoint, Alembic migrations |
| M3 | In progress | Report generation (HTML complete, PDF service complete, review status tracking) |
| M4 | Not started | AI-assisted data extraction and summarisation |

## High-Level Architecture

```
Browser SPA (frontend/)
        │  HTTP
        ▼
FastAPI Routes (app/routes/)
        │
        ▼
Pydantic Schemas (app/schemas/)  ← write-time validation
        │
        ▼
Services (app/services/)
  ├── CRUD services → SQLAlchemy Models → SQLite
  ├── evaluation.py → engine.run_evaluation() [pure, no DB]
  └── report_html.py / report_pdf.py → printable reports
                          │
                app/engine/
                  conditions.py
                  selector.py
                  scorer.py
                  report.py
```

## Project Structure

```
alembic/
  env.py                     # imports all models; render_as_batch=True for SQLite
  versions/
    *_initial_schema.py      # M1 baseline
    *_add_section_reference.py
    *_m3_add_review_status.py # adds review_status enum to rules
app/
  config.py                  # privacy_mode_enabled() reads PRIVACY_MODE env var
  database/
    base.py                  # shared DeclarativeBase
    session.py               # engine, SessionLocal, get_db dependency
    init_db.py               # create_all fallback (AUTO_CREATE_SCHEMA=1)
  engine/                    # pure functions — zero DB dependency
    conditions.py            # parse_condition_expression, evaluate_condition, missing_required_fields
    selector.py              # deduplicate_by_version (highest version per rule_code)
    scorer.py                # rule_score, category/jurisdiction breakdown, overall_score
    report.py                # run_evaluation() — entry point, composes sub-modules
  models/
    client.py                # Client (citizenships JSON, current_residency, is_deleted)
    residency_history.py     # ResidencyHistory (country, start/end date, client_id)
    asset.py                 # Asset (type, location, ownership_structure, client_id)
    knowledge_source.py      # KnowledgeSource (jurisdiction, title, url UNIQUE, source_type)
    rule.py                  # Rule (rule_code, version, condition_expression JSON, risk/confidence/category enums, review_status)
  routes/
    sources.py               # /sources CRUD
    rules.py                 # /rules CRUD + soft delete
    clients.py               # /clients — returns 403 in privacy mode
    assets.py                # /assets — returns 403 in privacy mode
    evaluation.py            # /evaluate/private, /evaluate/private/preview, /evaluate/private/report, /{client_id}, /rules/{code}/versions
  schemas/
    evaluation.py            # EvaluationRequest/Response, TriggeredRule, CategoryScore, Citation, IncompleteRule, PreviewResponse
    rule.py                  # RuleCreate with _validate_condition_node write-time validation
  services/
    evaluation.py            # fetches active rules, deduplicates by version, calls engine
    rules.py                 # CRUD + get_rule_versions
    sources.py, clients.py, assets.py
    report_html.py           # generate_report_html() — printable HTML assessment dossier
    report_pdf.py            # generate_report_pdf() — PDF assessment report via FPDF
  main.py                    # FastAPI app, lifespan, static mounts, router registration
frontend/
  core.js                    # API_BASE_URL, JURISDICTIONS, shared DOM element refs, apiRequest()
  navigation.js              # section switching, sidebar active state
  app.js                     # bootstrap, initial data load
  dashboard.js               # metric cards, sparklines, engine status
  evaluation.js              # private assessment worksheet — answers state, payload builder
  evaluation_config.js       # FIELD_MAP, GROUPS, PRESETS, FOCUS_OPTIONS, TAX_RESIDENCY_OPTIONS
  evaluation_views.js        # renderEvaluationResult(), renderPreviewResult()
  rules.js                   # rules table, create/delete modal
  sources.js                 # sources table, create modal
tests/
  conftest.py                # sys.path setup
  test_evaluator.py          # engine unit tests + schema validation
  test_http_integration.py   # live HTTP tests against a temp migrated DB
  test_regressions.py        # migration regression checks
index.html                   # SPA shell — loads all frontend/ modules
styles.css                   # consolidated stylesheet (design tokens, layout, components)
seed_data.py                 # populates sources and rules for development
seed_rules.py                # rule definitions for seeding
seed_sources.py              # knowledge source definitions for seeding
```

## Data Model

```
KNOWLEDGE_SOURCES ──< RULES
CLIENTS ──< RESIDENCY_HISTORY
    └───< ASSETS
```

Key constraints:
- `knowledge_source.url` — UNIQUE
- `(rule.rule_code, rule.version)` — UNIQUE
- `rule.source_id` — FK to `knowledge_sources`, required (every rule cites a source)

## Rule Model

Each rule carries:
- `rule_code` + `version` — unique pair; new versions are inserted, not updates
- `condition_expression` — structured JSON condition tree
- `risk_level` / `confidence_level` / `category` — enum fields for scoring
- `jurisdiction` — jurisdiction scope
- `effective_from` / `effective_to` — date-bounded applicability
- `is_deleted` — soft delete flag
- `review_status` — `verified_current`, `needs_update`, or `unsupported_or_wrong_source`

## Evaluation Engine

### Entry Point

```python
run_evaluation(client, rules, client_data) → dict
```

`rules` must already be filtered (active, date-bounded) and version-deduplicated before being passed in. `services/evaluation.py` handles that step.

### Active Rule Query

```python
Rule.is_deleted == False
AND Rule.effective_from <= today
AND (Rule.effective_to IS NULL OR Rule.effective_to >= today)
```

Then `deduplicate_by_version()` keeps the highest `version` per `rule_code`.

### Condition Format

```json
{ "field": "days_in_country", "operator": ">=", "value": 183 }
{ "all": [ <condition>, ... ] }
{ "any": [ <condition>, ... ] }
```

Groups nest arbitrarily. Missing `field` in `client_data` → rule reported as incomplete (not an error).

### Supported Operators

| Category | Operators |
|----------|-----------|
| Comparison | `>=` `<=` `==` `!=` `>` `<` |
| Membership | `in` `not_in` (bidirectional — works if actual or expected is a list) |
| String | `contains` `starts_with` (case-insensitive) |
| Nullness | `is_empty` `not_empty` (no `value` key required) |

### Incomplete Rules

Before evaluation, `missing_required_fields()` checks whether `client_data` contains all fields referenced by the condition tree. If any are missing, the rule is added to `incomplete_rules` with the list of missing fields — it is not evaluated and does not trigger.

### Risk Scoring

**Individual rule score:**
```
risk_weight:   low=1, medium=2, high=3
conf_weight:   low=0.6, medium=0.8, high=1.0
rule_score = (risk_weight / 3) × conf_weight × 100
```

**Overall numeric score:** Weighted average of category scores:

| Category | Weight |
|----------|--------|
| residency | 30% |
| tax | 30% |
| cross_border | 25% |
| structure | 15% |

**Overall risk tier:** `max(risk_level)` across triggered rules — conservative, not averaged.

### Citation Deduplication

Deduplicated by `(source_url, section_reference)` pair. Two rules citing the same source but different sections produce distinct citations — preserves full legislative traceability.

### Write-Time Validation

`RuleCreate` validates `condition_expression` before it reaches the database:
- Every node must be a valid leaf or `all`/`any` group
- `operator` must be in the supported set
- `is_empty`/`not_empty` may omit `value`; all others require it
- `effective_to` must not precede `effective_from`
- Error messages include the node path (e.g. `condition_expression.all[2].operator`)

### Runtime Failure Handling

Any `ValueError`/`TypeError`/`KeyError` during rule evaluation is caught. The rule is skipped and a message is appended to `warnings`. Evaluation never aborts due to a single bad rule.

## Report Generation

### HTML Reports

`POST /evaluate/private/report` runs a full evaluation and renders the result as a self-contained printable HTML page. Uses a dossier-inspired design (cream paper, navy ink, brand red accents). Includes:
- Summary header with overall risk and score
- Triggered rules with jurisdiction, risk, and category badges
- Category breakdown with progress bars
- Jurisdiction breakdown table
- Citations list with source references
- Incomplete rules section
- Warnings

### PDF Reports

`generate_report_pdf()` in `app/services/report_pdf.py` produces a PDF version using FPDF. Uses the same dossier palette. The PDF endpoint is not yet wired to a route.

## Frontend Architecture

Vanilla JS ES module SPA. No build step — modules are loaded directly by the browser via `<script type="module">`.

### Module Responsibilities

- `core.js` — `apiRequest()` wrapper, `JURISDICTIONS` constant, all DOM element refs (`elements`), `setStatus()`
- `navigation.js` — section show/hide, sidebar link active state, topbar title/subtitle
- `evaluation.js` — all assessment worksheet logic: tri-state answers (`Unknown`/`No`/`Yes`), jurisdiction focus chips, readiness panel, payload builder, export/import
- `evaluation_config.js` — static data: `FIELD_MAP` (question text, group, type), `GROUPS`, `PRESETS`, `FOCUS_OPTIONS`, `TAX_RESIDENCY_OPTIONS`
- `evaluation_views.js` — pure render functions: `renderEvaluationResult()` and `renderPreviewResult()` write DOM from API responses
- Per-section modules (`rules.js`, `sources.js`) — each owns its list fetch, filter, and CRUD modal independently

### Design System

Dark navy sidebar (`#0D1C32`), surface hierarchy for depth (no border lines), risk chips with fixed colour vocabulary (low=green, medium=amber, high=red), tabular-nums data alignment. Single consolidated `styles.css`.

## Key Design Decisions

### Flat `client_data` Dict for Evaluation

The evaluation endpoints accept `client_data` as a free-form dict rather than tying evaluation to the `Client` ORM schema. This keeps the engine decoupled from the data model — rules can reference any field, and the client model doesn't need to expand prematurely. Missing fields are reported as incomplete rules, not errors.

### `render_as_batch=True` in Alembic

SQLite does not support `ALTER TABLE`. Batch mode rewrites the table transparently. Set globally in `alembic/env.py` so all migrations work without per-migration workarounds.

### Rule Versioning

`rule_code` + `version` is the unique pair. New versions are inserted alongside old ones; old versions are never modified. The selector keeps the highest version per code for evaluation, while the version history endpoint exposes the full audit trail.

### Soft Delete

Rules and clients use `is_deleted = True` instead of physical deletion. Soft-deleted rules are excluded from evaluation queries.

### Review Status Tracking

Each rule carries a `review_status` field (`verified_current`, `needs_update`, `unsupported_or_wrong_source`) to track the validity of the underlying legal source. This status is propagated through the evaluation response and report output.

## Future Expansion

- Persistent evaluation result storage
- PDF report endpoint
- AI-assisted data extraction (Milestone 4)
- Full client data schema aligned with rule field references
- Residency timeline computation from `ResidencyHistory`
- Authentication and authorisation
- PostgreSQL via `DATABASE_URL`
- Rule supersession logic
