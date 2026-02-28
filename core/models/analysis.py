from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import pandas as pd
from typing import Any, List, Dict

from core.models.liquidity import LiquidityLevel

Swing = Tuple[pd.Timestamp, float, str]


@dataclass
class Bias:
    external: str
    internal: str


@dataclass
class StructureSnapshot:
    symbol: str
    timeframe: Optional[str]

    bias: Bias
    state: str

    bos_event: Optional[dict]
    momentum: int

    external_swings: List[Swing]
    internal_swings: List[Swing]

    current_price: float  # <-- add this
    range: dict  # {"high": float, "low": float} <-- add this

    # ---- NON-DEFAULT FIELDS FIRST ----
    liquidity_levels: List[LiquidityLevel]

    # ---- DEFAULT FIELDS AFTER ----
    zones: list = field(default_factory=list)


@dataclass
class TopdownSnapshot:
    symbol: str

    weekly: StructureSnapshot
    daily: StructureSnapshot
    h4: StructureSnapshot
    m15: StructureSnapshot

    dominant_bias: str
    alignment_score: int
    trade_context: str
    trade_allowed: bool


@dataclass
class TopDownSnapshot:
    symbol: str
    macro_bias: str
    alignment_score: int
    total_score: int
    is_aligned: bool
    timeframe_snapshots: Dict[str, StructureSnapshot]
