from dataclasses import dataclass


@dataclass
class Zone:
    type: str  # supply | demand
    origin: str  # bos_origin | base_pattern
    proximal: float
    distal: float
    created_at: any
    timeframe: str
