# SupplyChain Sentinel

## Event-Driven Inventory Risk & Operations Control Tower

> A production-oriented supply-chain platform that converts inventory events into explainable stock-out risk assessments, actionable operational alerts, and an auditable event history.

![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-D71F00)
![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/container-Docker-2496ED?logo=docker&logoColor=white)
![Python Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)

---

## Table of Contents

-   [Overview](#overview)
-   [Key Capabilities](#key-capabilities)
-   [Architecture](#architecture)
-   [How It Works](#how-it-works)
-   [Risk Engine](#risk-engine)
-   [API Reference](#api-reference)
-   [Data Model](#data-model)
-   [Project Structure](#project-structure)
-   [Getting Started](#getting-started)
-   [Running with Docker](#running-with-docker)
-   [Testing](#testing)
-   [Demo Scenario](#demo-scenario)
-   [Configuration](#configuration)
-   [Deployment](#deployment)
-   [Design Decisions](#design-decisions)
-   [Reliability and Safety](#reliability-and-safety)
-   [Future Improvements](#future-improvements)
-   [Resume / Portfolio Description](#resume--portfolio-description)
-   [License](#license)

------------------------------------------------------------------------

## Overview

Inventory systems are event-driven by nature: stock is received,
reserved, adjusted, and consumed continuously.

A reliable operations system must therefore do more than store the
current inventory level. It should answer:

-   What changed?
-   Was the event already processed?
-   Is the current inventory position at risk?
-   Why was the item classified as risky?
-   What action should the operations team take?
-   Can the decision be reconstructed later?

**SupplyChain Sentinel** addresses these requirements through four core
principles:

1.  **Idempotent event processing** --- duplicate events do not
    double-count inventory.
2.  **Explainable risk scoring** --- risk is calculated from explicit,
    inspectable business rules.
3.  **Operational alerting** --- warning and critical conditions
    generate actionable alerts.
4.  **Auditability** --- inventory changes, event processing, alert
    creation, and alert resolution are recorded.

------------------------------------------------------------------------

## Key Capabilities

  -----------------------------------------------------------------------
  Capability                          Description
  ----------------------------------- -----------------------------------
  Inventory management                Create and update SKU-level
                                      inventory positions

  Event ingestion                     Process received, reserved, and
                                      adjusted inventory events

  Idempotency                         Prevent duplicate event replays
                                      from mutating inventory twice

  Risk scoring                        Calculate a deterministic 0--100
                                      stock-out risk score

  Explainability                      Return the conditions that
                                      contributed to the risk score

  Alert generation                    Create warning/critical alerts with
                                      recommendations

  Alert resolution                    Resolve operational alerts through
                                      the API

  Audit logging                       Persist an event history for
                                      operational traceability

  Operations dashboard                View KPIs, inventory, alerts, and
                                      recent audit activity

  Demo environment                    Load/reset isolated critical,
                                      warning, and healthy scenarios

  Database portability                Use SQLite locally or PostgreSQL in
                                      a containerized environment

  API documentation                   Interactive OpenAPI/Swagger
                                      documentation through FastAPI
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## Architecture

``` text
                         ┌──────────────────────────┐
                         │   Operations Dashboard   │
                         │      /static/index.html  │
                         └────────────┬─────────────┘
                                      │ HTTP/JSON
                                      ▼
                         ┌──────────────────────────┐
                         │        FastAPI API       │
                         │                          │
                         │  Inventory Management    │
                         │  Event Processing        │
                         │  Alert Management        │
                         │  Dashboard APIs          │
                         └────────────┬─────────────┘
                                      │
                       ┌──────────────┼──────────────┐
                       ▼              ▼              ▼
                ┌────────────┐ ┌────────────┐ ┌────────────┐
                │ Risk Engine│ │ Audit Log  │ │   Alerts   │
                │  Rules     │ │  History   │ │ & Actions  │
                └────────────┘ └────────────┘ └────────────┘
                       │              │              │
                       └──────────────┼──────────────┘
                                      ▼
                         ┌──────────────────────────┐
                         │       SQL Database       │
                         │ SQLite / PostgreSQL      │
                         └──────────────────────────┘
```

### Request lifecycle

``` text
Inventory/Event Request
        │
        ▼
   Pydantic Validation
        │
        ▼
   SKU Lookup
        │
        ├── Unknown SKU ──► 404
        │
        ▼
 Idempotency Check
        │
        ├── Duplicate ──► Return existing state
        │
        ▼
 Apply Inventory Delta
        │
        ├── Negative stock ──► 409
        │
        ▼
   Risk Assessment
        │
        ├── Healthy ──► Audit
        │
        └── Warning/Critical
                  │
                  ├── Create Alert
                  └── Write Audit Entry
```

------------------------------------------------------------------------

## How It Works

### 1. Create or update an inventory position

An inventory position contains:

-   SKU
-   Product name
-   Current stock
-   Reorder point
-   Average daily demand
-   Supplier lead time

Example:

``` http
PUT /api/v1/inventory
```

``` json
{
  "sku": "IPAD-MINI-128-BLU",
  "product_name": "iPad Mini 128GB Blue",
  "on_hand": 28,
  "reorder_point": 30,
  "daily_demand": 12,
  "supplier_lead_days": 5
}
```

### 2. Ingest an inventory event

Supported event types:

-   `inventory_received`
-   `inventory_reserved`
-   `inventory_adjusted`

For example, reserving 8 units:

``` http
POST /api/v1/events
```

``` json
{
  "event_id": "evt-demo-2026-0001",
  "event_type": "inventory_reserved",
  "sku": "IPAD-MINI-128-BLU",
  "quantity": 8
}
```

The reservation decreases inventory by 8 units and immediately
recalculates risk.

### 3. Prevent duplicate processing

The `event_id` is uniquely constrained in the database.

If the exact same event is submitted again:

``` json
{
  "event_id": "evt-demo-2026-0001",
  "duplicate": true,
  "on_hand": 20,
  "risk_score": 100.0,
  "risk_level": "critical"
}
```

The event is not applied a second time.

This makes event replay safe and protects inventory state from duplicate
messages.

### 4. Generate an explainable assessment

The risk engine evaluates the updated inventory position and returns:

-   risk score
-   risk level
-   contributing factors
-   recommended action

Example:

``` json
{
  "risk_score": 100.0,
  "risk_level": "critical",
  "explanation": [
    "1.7 days of inventory coverage",
    "stock is at or below reorder point",
    "stock cannot cover expected supplier lead-time demand",
    "coverage is below the 3-day operating buffer"
  ]
}
```

------------------------------------------------------------------------

## Risk Engine

Risk is deliberately deterministic and transparent.

### Derived metrics

#### Lead-time demand

``` text
demand_during_lead = daily_demand × supplier_lead_days
```

#### Inventory coverage

``` text
coverage_days = on_hand ÷ daily_demand
```

### Scoring rules

  Condition                                        Score
  ---------------------------------------------- -------
  Stock is at or below reorder point                 +45
  Stock cannot cover supplier lead-time demand       +35
  Inventory coverage is below 3 days                 +20
  Maximum score                                      100

### Classification

  ------------------------------------------------------------------------
                         Score Level                 Operational
                                                     recommendation
  ---------------------------- --------------------- ---------------------
                        `< 40` Healthy               No action required

                       `40–69` Warning               Create a
                                                     replenishment request
                                                     within the next
                                                     business day

                        `≥ 70` Critical              Expedite
                                                     replenishment and
                                                     review alternate
                                                     supplier allocation
  ------------------------------------------------------------------------

The score is capped at `100`.

This approach is intentionally simple enough for an operations team to
understand and audit.

------------------------------------------------------------------------

## API Reference

FastAPI automatically exposes interactive API documentation.

### Core endpoints

  Method    Endpoint                              Purpose
  --------- ------------------------------------- -------------------------------------
  `GET`     `/health`                             Service health check
  `PUT`     `/api/v1/inventory`                   Create or update inventory
  `POST`    `/api/v1/events`                      Process an inventory event
  `GET`     `/api/v1/dashboard`                   Retrieve operational dashboard data
  `PATCH`   `/api/v1/alerts/{alert_id}/resolve`   Resolve an alert

### Demo endpoints

  --------------------------------------------------------------------------
  Method                  Endpoint                Purpose
  ----------------------- ----------------------- --------------------------
  `POST`                  `/api/v1/demo/load`     Load isolated
                                                  critical/warning/healthy
                                                  demo data

  `POST`                  `/api/v1/demo/reset`    Remove the demo data
  --------------------------------------------------------------------------

### Interactive documentation

Once the application is running:

``` text
Swagger UI: http://127.0.0.1:8000/docs
OpenAPI JSON: http://127.0.0.1:8000/openapi.json
```

------------------------------------------------------------------------

## Data Model

The application uses four primary database entities.

### `inventory`

Stores the current state of each SKU.

``` text
sku
product_name
on_hand
reorder_point
daily_demand
supplier_lead_days
updated_at
```

### `supply_events`

Stores processed inventory events.

``` text
id
event_id
event_type
sku
quantity
created_at
```

`event_id` has a unique database constraint to enforce idempotency.

### `alerts`

Stores operational risk alerts.

``` text
id
sku
severity
risk_score
recommendation
status
created_at
```

### `audit_logs`

Stores operational history.

``` text
id
action
subject
details
created_at
```

Audit details are serialized as JSON so event context can be
reconstructed later.

------------------------------------------------------------------------

## Project Structure

``` text
supplychain-sentinel/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and API routes
│   ├── database.py          # SQLAlchemy engine and session management
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── risk.py              # Deterministic inventory risk engine
│   │
│   └── static/
│       └── index.html       # Operations control-tower dashboard
│
├── examples/
│   └── demo.http            # Example API requests
│
├── tests/
│   └── test_api.py          # API and idempotency tests
│
├── .env.example             # Environment configuration template
├── Dockerfile               # Container image definition
├── docker-compose.yml       # API + PostgreSQL local stack
├── render.yaml              # Render deployment configuration
├── requirements.txt         # Python dependencies
└── README.md
```

------------------------------------------------------------------------

## Getting Started

### Prerequisites

-   Python 3.11+
-   `pip`
-   Git
-   Docker Desktop --- optional, for the PostgreSQL stack

### 1. Clone the repository

``` bash
git clone <your-repository-url>
cd supplychain-sentinel
```

### 2. Create a virtual environment

#### Windows PowerShell

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### macOS / Linux

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Start the API

``` bash
uvicorn app.main:app --reload
```

The application will be available at:

``` text
http://127.0.0.1:8000
```

Dashboard:

``` text
http://127.0.0.1:8000/
```

API documentation:

``` text
http://127.0.0.1:8000/docs
```

Health check:

``` text
http://127.0.0.1:8000/health
```

------------------------------------------------------------------------

## Running with Docker

The repository includes a production-like local stack with:

-   FastAPI application
-   PostgreSQL 16
-   Persistent PostgreSQL volume

Start the stack:

``` bash
docker compose up --build
```

Run in detached mode:

``` bash
docker compose up --build -d
```

Stop the stack:

``` bash
docker compose down
```

Stop the stack and remove persisted database data:

``` bash
docker compose down -v
```

The API remains available at:

``` text
http://127.0.0.1:8000
```

### Database configuration

The application selects its database from `DATABASE_URL`.

Without an environment variable, local development falls back to:

``` text
sqlite:///./sentinel.db
```

The Docker Compose stack configures PostgreSQL automatically.

------------------------------------------------------------------------

## Testing

Run the complete test suite with:

``` bash
pytest -q
```

The current tests cover important state-management guarantees,
including:

### Idempotency

The same event can be submitted twice without applying the inventory
mutation twice.

### Inventory protection

An event that would make inventory negative is rejected with HTTP
`409 Conflict`.

These tests protect two of the most important correctness properties of
the event-processing layer.

------------------------------------------------------------------------

## Demo Scenario

The application contains an isolated demo scenario designed for
demonstrations, portfolio reviews, and technical interviews.

Load the scenario:

``` bash
curl -X POST http://127.0.0.1:8000/api/v1/demo/load
```

The demo creates three independent SKUs:

  SKU                   Scenario
  --------------------- -----------------------------
  `DEMO-CRITICAL-001`   Critical inventory position
  `DEMO-WARNING-001`    Warning inventory position
  `DEMO-HEALTHY-001`    Healthy inventory position

The dashboard can then be opened at:

``` text
http://127.0.0.1:8000/
```

Reset only the demo data:

``` bash
curl -X POST http://127.0.0.1:8000/api/v1/demo/reset
```

The demo endpoints deliberately operate only on the reserved `DEMO-*`
SKUs and do not modify user-created inventory.

------------------------------------------------------------------------

## Configuration

Create a local `.env` file from the provided template when
environment-specific configuration is required.

Example:

``` env
DATABASE_URL=postgresql+psycopg://sentinel:sentinel@db:5432/sentinel
API_KEY=replace-me-in-production
```

### Environment variables

  -----------------------------------------------------------------------
  Variable                            Purpose
  ----------------------------------- -----------------------------------
  `DATABASE_URL`                      SQLAlchemy database connection
                                      string

  `API_KEY`                           Reserved configuration value for
                                      future API authentication
                                      integration
  -----------------------------------------------------------------------

> **Security note:** The current API does not enforce API-key
> authentication. Do not treat `API_KEY` as an implemented security
> boundary until authentication/authorization middleware is added.

------------------------------------------------------------------------

## Deployment

A `render.yaml` configuration is included for deployment to Render.

The service is configured to:

-   use Python 3.11
-   install dependencies from `requirements.txt`
-   start FastAPI with Uvicorn
-   expose `/health` as the health-check endpoint

### Production database recommendation

For production deployment, use managed PostgreSQL rather than local
SQLite.

Configure:

``` env
DATABASE_URL=<managed-postgresql-connection-string>
```

The application already uses SQLAlchemy and Psycopg, so the database
backend can be switched through configuration without changing the
domain logic.

### Production hardening checklist

Before production use, add:

-   API authentication
-   Role-based authorization
-   Secret management
-   Database migrations with Alembic
-   Structured application logging
-   Request correlation IDs
-   Rate limiting
-   CORS policy
-   HTTPS enforcement
-   Database backups
-   Monitoring and alerting
-   CI/CD checks
-   Stronger integration and concurrency tests

------------------------------------------------------------------------

## Design Decisions

### Why deterministic risk rules instead of an ML model?

Inventory risk is a business-critical operational decision. The first
version prioritizes:

-   transparency
-   predictable behavior
-   easy validation
-   deterministic testing
-   operational explainability

A machine-learning model could be introduced later for forecasting or
anomaly detection while keeping the final operational policy explainable
and governed.

### Why idempotency at the event layer?

Distributed systems can deliver the same event more than once.

If an inventory reservation is accidentally processed twice, the
resulting stock level becomes incorrect.

SupplyChain Sentinel therefore treats `event_id` as an idempotency key
and persists it with a unique constraint.

### Why separate events from inventory state?

`Inventory` represents the current state.

`SupplyEvent` represents what happened.

Keeping those concepts separate allows the system to:

-   maintain an operational snapshot
-   preserve event history
-   audit changes
-   reason about replay behavior
-   evolve toward event-driven integrations

### Why SQLAlchemy?

SQLAlchemy provides a database abstraction layer while allowing the same
application code to work with SQLite for lightweight development and
PostgreSQL for a more production-oriented deployment.

------------------------------------------------------------------------

## Reliability and Safety

SupplyChain Sentinel includes several safeguards around inventory
correctness.

### Input validation

Pydantic validates:

-   SKU and product-name lengths
-   non-negative inventory values
-   positive demand
-   non-negative supplier lead time
-   positive event quantities
-   supported event types

### Negative inventory prevention

Inventory mutations that would result in:

``` text
on_hand < 0
```

are rejected with HTTP `409 Conflict`.

### Idempotent event replay

Duplicate `event_id` values do not mutate inventory again.

### Audit trail

Important state transitions create audit records, including:

-   inventory creation/update
-   event processing
-   alert creation
-   alert resolution
-   demo data loading

### Demo isolation

Demo operations are scoped to predefined `DEMO-*` SKUs, preventing the
demo workflow from deleting unrelated inventory.

------------------------------------------------------------------------

## Future Improvements

The current architecture provides a foundation for a larger supply-chain
platform.

Potential next iterations include:

### Event infrastructure

-   Kafka or Redpanda integration
-   Outbox pattern
-   Dead-letter queues
-   Retry policies
-   Exactly-once-effect processing semantics

### Supply-chain intelligence

-   Demand forecasting
-   Supplier reliability scoring
-   Safety-stock optimization
-   Purchase-order ETA prediction
-   Lead-time variability analysis
-   Multi-echelon inventory optimization

### Platform engineering

-   Alembic migrations
-   Redis-backed caching
-   Background workers
-   OpenTelemetry tracing
-   Prometheus metrics
-   Grafana dashboards
-   CI/CD pipeline
-   Automated security scanning

### Security

-   OAuth2/OIDC
-   JWT-based authentication
-   RBAC
-   Tenant isolation
-   Secret management
-   Audit-log integrity controls

### Operations

-   Slack/email alert integrations
-   Alert ownership
-   Escalation policies
-   Alert deduplication
-   SLA tracking
-   Incident workflows

------------------------------------------------------------------------

## Resume / Portfolio Description

### One-line description

> **SupplyChain Sentinel** --- Event-driven inventory risk control tower
> with FastAPI, SQLAlchemy, PostgreSQL, Docker, idempotent event
> processing, explainable risk scoring, operational alerts, and an
> auditable event trail.

### Resume bullet

> Built an event-driven inventory risk platform using FastAPI,
> SQLAlchemy, PostgreSQL, and Docker; implemented idempotent event
> processing, deterministic 0--100 stock-out risk scoring, automated
> alerts, negative-inventory safeguards, and auditable state transitions
> through an operations dashboard.

------------------------------------------------------------------------

## License

This project is intended as a portfolio and engineering demonstration
project.

Add your preferred open-source license before public production
distribution, for example MIT, Apache-2.0, or an organization-specific
license.
