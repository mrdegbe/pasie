# core/analysis/supply_demand/models.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class SupplyDemandZone:
    type: str  # "supply" or "demand"
    start_price: float
    end_price: float
    start_index: int
    end_index: int
    timeframe: str
    swept: bool = False
