# ClearPath Global — Risk Intelligence Platform

Rules-based cross-border risk intelligence for advisory teams. Privacy-first by default: rules and knowledge sources are persisted, but client financial facts are evaluated statelessly and never stored. Generates professional HTML and PDF assessment reports.

## Stack

- Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2
- SQLite (default) via `risk_intelligence.db`
- Vanilla JavaScript SPA served by FastAPI
- FPDF2 for PDF report generation

## Privacy Model

`PRIVACY_MODE=1` is the default. When enabled:

- Client financial payloads are evaluated in memory and returned to the browser — never written to the database.
- `/clients` and `/assets` routes return `403`.
- Repeatability is handled via local JSON export/import in the browser.
- `PRIVACY_MODE=0` re-enables persistent client/asset routes for local development.

## Run Locally

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe .\seed_data.py
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- App: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`

## Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| `PRIVACY_MODE` | `1` | `0` re-enables persistent client/asset routes |
| `DATABASE_URL` | `sqlite:///./risk_intelligence.db` | Overrides database location |
| `AUTO_CREATE_SCHEMA` | unset | `1` calls `create_all()` at startup as a dev fallback |

## API Endpoints

### Sources
- `GET /sources` — list knowledge sources
- `POST /sources` — create knowledge source

### Rules
- `GET /rules` — list rules
- `POST /rules` — create rule
- `DELETE /rules/{id}` — soft delete

### Private Evaluation
- `POST /evaluate/private` — full stateless evaluation (score, breakdown, citations)
- `POST /evaluate/private/preview` — matched/unmatched rules with reasons, no scoring
- `POST /evaluate/private/report` — generates printable HTML assessment report
- `GET /evaluate/rules/{rule_code}/versions` — full version history

### Client Evaluation (blocked in privacy mode)
- `POST /evaluate/{client_id}` — evaluate against a stored client
- `POST /evaluate/{client_id}/preview` — preview rule matching for a stored client
- `GET/POST /clients`, `DELETE /clients/{id}`
- `GET/POST /assets`

### System
- `GET /health`
- `GET /` — serves the browser SPA

## Stateless Evaluation Payload

```json
POST /evaluate/private
{
  "assessment_label": "Matter 24-017",
  "client_data": {
    "days_in_country": 190,
    "citizenship": "US",
    "tax_residency_status": "resident",
    "foreign_source_income": 145000
  }
}
```

Response includes `overall_risk`, `score` (0–100), `triggered_rules`, `summary` (with `review_status` per rule), `category_breakdown`, `jurisdiction_breakdown`, `citations`, `incomplete_rules` (rules skipped due to missing data), and `warnings` for any malformed rules.

## Testing

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Test coverage: engine unit tests (conditions, scoring, version dedup, report assembly), schema write-time validation, privacy-mode route behavior, migration regressions, live HTTP integration tests against a temporary migrated database.

## What Is Not Yet Implemented

- Authentication and authorisation
- Persistent evaluation result storage
- Background processing
- PDF report endpoint (service exists, endpoint not yet wired)
- AI-assisted data extraction (Milestone 4)
