from dataclasses import dataclass
from typing import List, Tuple, Optional
import pandas as pd


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

    supply_zones: List
    demand_zones: List


@dataclass
class StructureContext:
    symbol: str
    timeframe: str
    swings: list
    cleaned_swings: list
    direction: str
    bos: dict | None
    momentum_score: int
    supply_zones: list
    demand_zones: list


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


# from dataclasses import dataclass
# from typing import List, Tuple, Optional
# import pandas as pd


# Swing = Tuple[pd.Timestamp, float, str]


# @dataclass
# class StructureSnapshot:
#     symbol: str
#     timeframe: str

#     external_direction: str
#     internal_direction: str
#     state: str

#     bos: Optional[dict]
#     momentum_score: int

#     external_swings: List[Swing]
#     internal_swings: List[Swing]
