from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class InventoryInput(BaseModel):
    sku: str = Field(min_length=2, max_length=80)
    product_name: str = Field(min_length=2, max_length=160)
    on_hand: int = Field(ge=0)
    reorder_point: int = Field(ge=0)
    daily_demand: float = Field(gt=0)
    supplier_lead_days: int = Field(ge=0)


class EventInput(BaseModel):
    event_id: str = Field(min_length=8, max_length=100)
    event_type: Literal["inventory_received", "inventory_reserved", "inventory_adjusted"]
    sku: str
    quantity: int = Field(gt=0)


class EventResult(BaseModel):
    event_id: str
    duplicate: bool
    on_hand: int
    risk_score: float
    risk_level: str
    explanation: list[str]


class AlertView(BaseModel):
    id: int
    sku: str
    severity: str
    risk_score: float
    recommendation: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

