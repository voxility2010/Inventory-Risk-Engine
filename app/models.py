from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Inventory(Base):
    __tablename__ = "inventory"
    sku: Mapped[str] = mapped_column(String(80), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(160))
    on_hand: Mapped[int] = mapped_column(Integer, default=0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=10)
    daily_demand: Mapped[float] = mapped_column(Float, default=1.0)
    supplier_lead_days: Mapped[int] = mapped_column(Integer, default=7)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SupplyEvent(Base):
    __tablename__ = "supply_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_event_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(40))
    sku: Mapped[str] = mapped_column(String(80))
    quantity: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(20))
    risk_score: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(80))
    subject: Mapped[str] = mapped_column(String(100))
    details: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

