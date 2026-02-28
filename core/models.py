from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import pandas as pd
from typing import Any, List, Dict

Swing = Tuple[pd.Timestamp, float, str]


@dataclass
class Bias:
    external: str
    internal: str


@dataclass
class LiquidityLevel:
    price: float
    liquidity_type: str  # "equal_high", "equal_low", "swing_high", "swing_low"
    timeframe: str
    indices: List[int] = field(default_factory=list)
    swept: bool = False
    swept_at_index: Optional[int] = None


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


@dataclass
class Setup:
    symbol: str
    direction: str  # 'bullish' / 'bearish'
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence_score: int


@dataclass
class SupplyDemandZone:
    type: str  # "supply" or "demand"
    start_price: float
    end_price: float
    start_index: int
    end_index: int
    timeframe: str
    swept: bool = False
