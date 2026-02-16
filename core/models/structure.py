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
