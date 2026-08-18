import os
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_sentinel.db"
from app.main import app

client = TestClient(app)


def test_inventory_event_is_idempotent():
    sku = "TEST-SKU-001"
    response = client.put("/api/v1/inventory", json={"sku": sku, "product_name": "Test part", "on_hand": 10, "reorder_point": 8, "daily_demand": 4, "supplier_lead_days": 3})
    assert response.status_code == 201
    event = {"event_id": "test-event-unique-001", "event_type": "inventory_reserved", "sku": sku, "quantity": 2}
    first = client.post("/api/v1/events", json=event)
    second = client.post("/api/v1/events", json=event)
    assert first.status_code == 201
    assert first.json()["duplicate"] is False
    assert first.json()["on_hand"] == 8
    assert second.status_code == 201
    assert second.json()["duplicate"] is True
    assert second.json()["on_hand"] == 8


def test_negative_inventory_is_rejected():
    client.put("/api/v1/inventory", json={"sku": "TEST-SKU-002", "product_name": "Test part", "on_hand": 1, "reorder_point": 1, "daily_demand": 1, "supplier_lead_days": 1})
    response = client.post("/api/v1/events", json={"event_id": "test-event-unique-002", "event_type": "inventory_reserved", "sku": "TEST-SKU-002", "quantity": 2})
    assert response.status_code == 409

