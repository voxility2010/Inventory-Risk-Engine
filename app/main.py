import json
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Alert, AuditLog, Inventory, SupplyEvent
from .risk import assess_risk
from .schemas import AlertView, EventInput, EventResult, InventoryInput


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SupplyChain Sentinel",
    version="1.0.0",
    description="Event-driven inventory risk monitoring with explainable alerts and an auditable audit trail.",
)

DEMO_SKUS = {
    "DEMO-CRITICAL-001",
    "DEMO-WARNING-001",
    "DEMO-HEALTHY-001",
}

STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


def audit(db: Session, action: str, subject: str, details: dict):
    db.add(
        AuditLog(
            action=action,
            subject=subject,
            details=json.dumps(details),
        )
    )


def process_event_record(db: Session, payload: EventInput):
    existing = db.scalar(
        select(SupplyEvent).where(SupplyEvent.event_id == payload.event_id)
    )

    item = db.get(Inventory, payload.sku)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown SKU. Create inventory before sending events.",
        )

    # Idempotency: replaying the same event does not mutate inventory again.
    if existing:
        assessment = assess_risk(item)
        return EventResult(
            event_id=payload.event_id,
            duplicate=True,
            on_hand=item.on_hand,
            risk_score=assessment.score,
            risk_level=assessment.level,
            explanation=assessment.explanation,
        )

    if payload.event_type == "inventory_received":
        delta = payload.quantity
    elif payload.event_type == "inventory_adjusted":
        delta = payload.quantity
    else:
        delta = -payload.quantity

    if item.on_hand + delta < 0:
        raise HTTPException(
            status_code=409,
            detail="Event would make inventory negative",
        )

    item.on_hand += delta
    db.add(SupplyEvent(**payload.model_dump()))

    assessment = assess_risk(item)

    audit(
        db,
        "event.processed",
        payload.sku,
        {
            **payload.model_dump(),
            "on_hand_after": item.on_hand,
            "risk_score": assessment.score,
            "risk_level": assessment.level,
            "explanation": assessment.explanation,
        },
    )

    if assessment.level in {"critical", "warning"}:
        db.add(
            Alert(
                sku=item.sku,
                severity=assessment.level,
                risk_score=assessment.score,
                recommendation=assessment.recommendation,
            )
        )

        audit(
            db,
            "alert.created",
            item.sku,
            {
                "severity": assessment.level,
                "risk_score": assessment.score,
                "recommendation": assessment.recommendation,
            },
        )

    return EventResult(
        event_id=payload.event_id,
        duplicate=False,
        on_hand=item.on_hand,
        risk_score=assessment.score,
        risk_level=assessment.level,
        explanation=assessment.explanation,
    )


@app.get("/", include_in_schema=False)
def dashboard():
    # Use an absolute path based on this file, not the process working directory.
    # Also disable caching so the browser always receives the current dashboard.
    return FileResponse(
        STATIC_INDEX,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "supplychain-sentinel"}


@app.put("/api/v1/inventory", status_code=201)
def upsert_inventory(
    payload: InventoryInput,
    db: Session = Depends(get_db),
):
    item = db.get(Inventory, payload.sku)

    if item is None:
        item = Inventory(**payload.model_dump())
        db.add(item)
        action = "inventory.created"
    else:
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
        action = "inventory.updated"

    audit(db, action, payload.sku, payload.model_dump())
    db.commit()

    return {
        "sku": item.sku,
        "on_hand": item.on_hand,
    }


@app.post(
    "/api/v1/events",
    response_model=EventResult,
    status_code=201,
)
def process_event(
    payload: EventInput,
    db: Session = Depends(get_db),
):
    result = process_event_record(db, payload)
    db.commit()
    return result


@app.post("/api/v1/demo/load")
def load_demo(db: Session = Depends(get_db)):
    """
    Load three isolated demo SKUs:
    - critical
    - warning
    - healthy

    Existing recruiter/user-created SKUs are never touched.
    """

    # Make repeated demo loads deterministic.
    for sku in DEMO_SKUS:
        db.execute(delete(Alert).where(Alert.sku == sku))
        db.execute(delete(AuditLog).where(AuditLog.subject == sku))
        db.execute(delete(SupplyEvent).where(SupplyEvent.sku == sku))
        db.execute(delete(Inventory).where(Inventory.sku == sku))

    demo_inventory = [
        Inventory(
            sku="DEMO-CRITICAL-001",
            product_name="iPad Mini 128GB Blue",
            on_hand=28,
            reorder_point=30,
            daily_demand=12,
            supplier_lead_days=5,
        ),
        Inventory(
            sku="DEMO-WARNING-001",
            product_name="USB-C Docking Station",
            on_hand=50,
            reorder_point=45,
            daily_demand=8,
            supplier_lead_days=5,
        ),
        Inventory(
            sku="DEMO-HEALTHY-001",
            product_name="Wireless Keyboard",
            on_hand=120,
            reorder_point=25,
            daily_demand=5,
            supplier_lead_days=4,
        ),
    ]

    db.add_all(demo_inventory)

    for item in demo_inventory:
        audit(
            db,
            "demo.inventory.loaded",
            item.sku,
            {
                "product_name": item.product_name,
                "on_hand": item.on_hand,
                "reorder_point": item.reorder_point,
                "daily_demand": item.daily_demand,
                "supplier_lead_days": item.supplier_lead_days,
            },
        )

    db.flush()

    critical = process_event_record(
        db,
        EventInput(
            event_id="demo-event-critical-0001",
            event_type="inventory_reserved",
            sku="DEMO-CRITICAL-001",
            quantity=8,
        ),
    )

    warning = process_event_record(
        db,
        EventInput(
            event_id="demo-event-warning-0001",
            event_type="inventory_reserved",
            sku="DEMO-WARNING-001",
            quantity=5,
        ),
    )

    healthy = process_event_record(
        db,
        EventInput(
            event_id="demo-event-healthy-0001",
            event_type="inventory_received",
            sku="DEMO-HEALTHY-001",
            quantity=10,
        ),
    )

    db.commit()

    return {
        "message": "Demo scenario loaded",
        "scenario": "critical + warning + healthy inventory",
        "results": [
            critical.model_dump(),
            warning.model_dump(),
            healthy.model_dump(),
        ],
    }


@app.post("/api/v1/demo/reset")
def reset_demo(db: Session = Depends(get_db)):
    for sku in DEMO_SKUS:
        db.execute(delete(Alert).where(Alert.sku == sku))
        db.execute(delete(AuditLog).where(AuditLog.subject == sku))
        db.execute(delete(SupplyEvent).where(SupplyEvent.sku == sku))
        db.execute(delete(Inventory).where(Inventory.sku == sku))

    db.commit()

    return {
        "message": "Demo data reset",
        "removed_skus": len(DEMO_SKUS),
    }


@app.get("/api/v1/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    alerts = db.scalars(
        select(Alert)
        .where(Alert.status == "open")
        .order_by(Alert.created_at.desc())
        .limit(10)
    ).all()

    audit_logs = db.scalars(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(15)
    ).all()

    inventory = db.scalars(
        select(Inventory).order_by(Inventory.updated_at.desc())
    ).all()

    return {
        "kpis": {
            "skus": db.scalar(select(func.count()).select_from(Inventory)) or 0,
            "open_alerts": len(alerts),
            "events_processed": db.scalar(
                select(func.count()).select_from(SupplyEvent)
            )
            or 0,
        },
        "alerts": [
            AlertView.model_validate(a).model_dump(mode="json")
            for a in alerts
        ],
        "inventory": [
            {
                "sku": item.sku,
                "product_name": item.product_name,
                "on_hand": item.on_hand,
                "reorder_point": item.reorder_point,
                "daily_demand": item.daily_demand,
                "supplier_lead_days": item.supplier_lead_days,
                "risk": assess_risk(item).level,
                "risk_score": assess_risk(item).score,
            }
            for item in inventory[:20]
        ],
        "audit_log": [
            {
                "action": x.action,
                "subject": x.subject,
                "details": json.loads(x.details),
                "created_at": x.created_at.isoformat(),
            }
            for x in audit_logs
        ],
    }


@app.patch("/api/v1/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.get(Alert, alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    if alert.status == "resolved":
        return {
            "id": alert_id,
            "status": "resolved",
        }

    alert.status = "resolved"

    audit(
        db,
        "alert.resolved",
        alert.sku,
        {"alert_id": alert_id},
    )

    db.commit()

    return {
        "id": alert_id,
        "status": "resolved",
    }