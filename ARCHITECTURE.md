# ClearPath Global — Architecture

Rules-based cross-border risk intelligence MVP. Stores workspaces, versioned rules, and knowledge sources. Evaluates client financial facts statelessly — no persistent client data in default (privacy) mode.

## Milestone State

| Milestone | Status | Scope |
|-----------|--------|-------|
| M1 | Complete | Multi-tenant foundation, versioned rules, knowledge source traceability, seed data |
| M2 | Complete | Modular rules engine, numeric scoring, category/jurisdiction breakdown, citations, preview endpoint, Alembic migrations |
| M3 | Not started | Report generation |
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
  └── evaluation.py → engine.run_evaluation() [pure, no DB]
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
app/
  config.py                  # privacy_mode_enabled() reads PRIVACY_MODE env var
  database/
    base.py                  # shared DeclarativeBase
    session.py               # engine, SessionLocal, get_db dependency
    init_db.py               # create_all fallback (AUTO_CREATE_SCHEMA=1)
  engine/                    # pure functions — zero DB dependency
    conditions.py            # parse_condition_expression, evaluate_condition, evaluate_rule
    selector.py              # deduplicate_by_version (highest version per rule_code)
    scorer.py                # rule_score, category/jurisdiction breakdown, overall_score
    report.py                # run_evaluation() — entry point, composes sub-modules
  models/
    tenant.py                # Tenant (name UNIQUE)
    client.py                # Client (citizenships JSON, current_residency, tenant_id, is_deleted)
    residency_history.py     # ResidencyHistory (country, start/end date, client_id)
    asset.py                 # Asset (type, location, ownership_structure, client_id)
    knowledge_source.py      # KnowledgeSource (jurisdiction, title, url UNIQUE, source_type)
    rule.py                  # Rule (rule_code, version, condition_expression JSON, risk/confidence/category enums)
  routes/
    tenants.py
    sources.py
    rules.py
    clients.py               # returns 403 in privacy mode
    assets.py                # returns 403 in privacy mode
    evaluation.py            # /evaluate/private, /evaluate/private/preview, /{client_id}, /rules/{code}/versions
  schemas/
    evaluation.py            # EvaluationRequest/Response, TriggeredRule, CategoryScore, Citation, PreviewResponse
    rule.py                  # RuleCreate with _validate_condition_node write-time validation
  services/
    evaluation.py            # fetches active rules, deduplicates by version, calls engine
    rules.py                 # CRUD + get_rule_versions
    tenants.py               # create/list/delete
    sources.py, clients.py, assets.py
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
  tenants.js                 # workspace list, create/delete modal
  clients.js                 # client table (blocked in privacy mode)
  assets.js                  # asset table (blocked in privacy mode)
tests/
  conftest.py                # sys.path setup
  test_evaluator.py          # engine unit tests + schema validation
  test_http_integration.py   # live HTTP tests against a temp migrated DB
  test_regressions.py        # migration regression checks
index.html                   # SPA shell — loads all frontend/ modules
styles.css                   # legacy monolithic stylesheet
styles/                      # split stylesheets (tokens, sidebar, buttons, etc.)
seed_data.py                 # populates tenants, sources, rules for development
```

## Data Model

```
TENANTS ──< CLIENTS ──< RESIDENCY_HISTORY
                  └───< ASSETS
KNOWLEDGE_SOURCES ──< RULES
```

Key constraints:
- `tenant.name` — UNIQUE
- `knowledge_source.url` — UNIQUE
- `(rule.rule_code, rule.version)` — UNIQUE
- `rule.source_id` — FK to `knowledge_sources`, required (every rule cites a source)

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

Groups nest arbitrarily. Missing `field` in `client_data` → `False` (never an error).

### Supported Operators

| Category | Operators |
|----------|-----------|
| Comparison | `>=` `<=` `==` `!=` `>` `<` |
| Membership | `in` `not_in` (bidirectional — works if actual or expected is a list) |
| String | `contains` `starts_with` (case-insensitive) |
| Nullness | `is_empty` `not_empty` (no `value` key required) |

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

## Frontend Architecture

Vanilla JS ES module SPA. No build step — modules are loaded directly by the browser.

### Module Responsibilities

- `core.js` — `apiRequest()` wrapper, `JURISDICTIONS` constant, all DOM element refs (`elements`), `setStatus()`
- `navigation.js` — section show/hide, sidebar link active state, topbar title/subtitle
- `evaluation.js` — all assessment worksheet logic: tri-state answers (`Unknown`/`No`/`Yes`), jurisdiction focus chips, readiness panel, payload builder, export/import
- `evaluation_config.js` — static data: `FIELD_MAP` (question text, group, type), `GROUPS`, `PRESETS`, `FOCUS_OPTIONS`, `TAX_RESIDENCY_OPTIONS`
- `evaluation_views.js` — pure render functions: `renderEvaluationResult()` and `renderPreviewResult()` write DOM from API responses
- Per-section modules (`rules.js`, `sources.js`, etc.) — each owns its list fetch, filter, and CRUD modal independently

### Design System

Dark navy sidebar (`#0D1C32`), surface hierarchy for depth (no border lines), risk chips with fixed colour vocabulary (low=green, medium=amber, high=red), tabular-nums data alignment.

## Key Design Decisions

### Flat `client_data` Dict for Evaluation

The evaluation endpoints accept `client_data` as a free-form dict rather than tying evaluation to the `Client` ORM schema. This keeps the engine decoupled from the data model — rules can reference any field, and the client model doesn't need to expand prematurely. Missing fields evaluate to `False`, not an error.

### `render_as_batch=True` in Alembic

SQLite does not support `ALTER TABLE`. Batch mode rewrites the table transparently. Set globally in `alembic/env.py` so all migrations work without per-migration workarounds.

### Rule Versioning

`rule_code` + `version` is the unique pair. New versions are inserted alongside old ones; old versions are never modified. The selector keeps the highest version per code for evaluation, while the version history endpoint exposes the full audit trail.

### Soft Delete

Rules and clients use `is_deleted = True` instead of physical deletion. Soft-deleted rules are excluded from evaluation queries.

## Open Questions

- **Evaluation result persistence** — should assessment outputs be stored per-client for audit history, or remain transient? Answer determines whether an `evaluation_results` table is needed before Milestone 3.

## Future Expansion

- Persistent evaluation result storage
- Report generation (Milestone 3)
- AI-assisted data extraction (Milestone 4)
- Full client data schema aligned with rule field references
- Residency timeline computation from `ResidencyHistory`
- Tenant-scoped authentication
- PostgreSQL via `DATABASE_URL`
- Rule supersession logic
