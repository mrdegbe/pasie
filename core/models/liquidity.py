# core/liquidity/models.py

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LiquidityLevel:
    price: float
    liquidity_type: str  # "equal_high", "equal_low", "swing_high", "swing_low"
    timeframe: str
    indices: List[int] = field(default_factory=list)
    swept: bool = False
    swept_at_index: Optional[int] = None
