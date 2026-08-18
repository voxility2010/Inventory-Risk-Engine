# SupplyChain Sentinel

An event-driven inventory-risk control tower. Operations teams can ingest inventory and purchase-order events, identify stock-out risks, and review an auditable recommendation trail.

## Why this project

This is designed as an enterprise systems project: idempotent event ingestion, explicit state transitions, explainable risk rules, and reliable audit logging. It deliberately does not depend on an LLM for critical decisions.

## Architecture

```text
Client / dashboard -> FastAPI -> PostgreSQL
                             -> Redis + RQ worker (optional async processing)
                             -> audit log + alerts
```

## Run locally

Requires Python 3.11+.

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API. The dashboard is at `http://127.0.0.1:8000/`.

To run the production-like stack:

```bash
docker compose up --build
```

## Core API flow

1. `POST /api/v1/inventory` creates or updates stock.
2. `POST /api/v1/events` accepts an idempotent inventory or purchase-order event.
3. The event is processed, a risk score is calculated, and alerts are created when needed.
4. `GET /api/v1/dashboard` provides operational KPIs, alerts, and recent audit history.

An example request is in `examples/demo.http`.

## Engineering choices to discuss in interviews

- **Idempotency:** Event IDs are unique; replaying an event returns the original result without mutating inventory twice.
- **Explainability:** The risk engine exposes its factors rather than returning an opaque ML score.
- **Auditability:** Every inventory update and generated recommendation becomes an immutable audit record.
- **Graceful evolution:** SQLite enables one-command local development; Docker switches to PostgreSQL with no application code changes.
- **Security-ready:** API keys are loaded from environment variables and the API has a clean dependency boundary for RBAC.

## Resume bullet

> Built SupplyChain Sentinel, an event-driven inventory-risk control tower with FastAPI, PostgreSQL, Redis, and Docker; implemented idempotent event handling, explainable stock-out alerts, and an immutable audit trail exposed through an operations dashboard.

