from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StructureContext:
    symbol: str
    timeframe: str
    swings: List
    cleaned_swings: List
    direction: str
    bos: Optional[dict]
    momentum_score: int
