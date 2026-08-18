from dataclasses import dataclass
from .models import Inventory


@dataclass
class RiskAssessment:
    score: float
    level: str
    explanation: list[str]
    recommendation: str


def assess_risk(item: Inventory) -> RiskAssessment:
    demand_during_lead = item.daily_demand * item.supplier_lead_days
    coverage_days = item.on_hand / item.daily_demand
    factors: list[str] = [f"{coverage_days:.1f} days of inventory coverage"]
    score = 0.0
    if item.on_hand <= item.reorder_point:
        score += 45
        factors.append("stock is at or below reorder point")
    if item.on_hand < demand_during_lead:
        score += 35
        factors.append("stock cannot cover expected supplier lead-time demand")
    if coverage_days < 3:
        score += 20
        factors.append("coverage is below the 3-day operating buffer")
    score = min(score, 100.0)
    if score >= 70:
        return RiskAssessment(score, "critical", factors, f"Expedite replenishment for {item.sku} and review alternate supplier allocation.")
    if score >= 40:
        return RiskAssessment(score, "warning", factors, f"Create a replenishment request for {item.sku} within the next business day.")
    return RiskAssessment(score, "healthy", factors, f"No action required for {item.sku}.")

