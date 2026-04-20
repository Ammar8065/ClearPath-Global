# ClearPath Global — Risk Intelligence Platform

Rules-based cross-border risk intelligence for advisory teams. Privacy-first by default: workspace, rule, and source data are persisted, but client financial facts are evaluated statelessly and never stored.

## Stack

- Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2
- SQLite (default) via `risk_intelligence.db`
- Vanilla JavaScript SPA served by FastAPI

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

### Tenants
- `GET /tenants` — list workspaces
- `POST /tenants` — create workspace
- `DELETE /tenants/{id}`

### Sources
- `GET /sources`
- `POST /sources`

### Rules
- `GET /rules`
- `POST /rules`
- `DELETE /rules/{id}` — soft delete

### Private Evaluation
- `POST /evaluate/private` — full stateless evaluation (score, breakdown, citations)
- `POST /evaluate/private/preview` — matched/unmatched rules with reasons, no scoring
- `GET /evaluate/rules/{rule_code}/versions` — full version history

### Legacy (blocked in privacy mode)
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

Response includes `overall_risk`, `score` (0–100), `triggered_rules`, `category_breakdown`, `jurisdiction_breakdown`, `citations`, and `warnings` for any malformed rules that were skipped.

## Testing

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Test coverage: engine unit tests (conditions, scoring, version dedup, report assembly), schema write-time validation, privacy-mode route behavior, live HTTP integration tests against a temporary migrated database.

## What Is Not Yet Implemented

- Authentication and authorisation
- Persistent evaluation result storage
- Background processing
- Report generation (Milestone 3)
- AI-assisted data extraction (Milestone 4)
