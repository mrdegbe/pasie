# core/analysis/supply_demand/engine.py

import pandas as pd
from typing import List

from core.models import SupplyDemandZone
from core.utils import find_swings, strict_alternation_structure


class SupplyDemandEngine:

    def __init__(self, timeframe: str, lookback: int = 20, tolerance: float = 0.0005):
        self.timeframe = timeframe
        self.lookback = lookback
        self.tolerance = tolerance

    def detect_zones(self, df: pd.DataFrame) -> List[SupplyDemandZone]:
        """
        Detects supply/demand zones based on structure and recent swings.
        """

        zones: List[SupplyDemandZone] = []

        # 1️⃣ Detect swings
        swings = strict_alternation_structure(find_swings(df, self.lookback))

        # 2️⃣ Identify potential zones
        for i in range(1, len(swings) - 1):
            prev_swing = swings[i - 1]
            swing = swings[i]
            next_swing = swings[i + 1]

            time, price, swing_type = swing

            # -----------------------------------
            # Demand Zone: low swing followed by bullish move
            # -----------------------------------
            if swing_type == "low" and next_swing[2] == "high":
                zone_start = price
                zone_end = min(prev_swing[1], next_swing[1])
                zones.append(
                    SupplyDemandZone(
                        type="demand",
                        start_price=zone_start,
                        end_price=zone_end,
                        start_index=i,
                        end_index=i + 1,
                        timeframe=self.timeframe,
                    )
                )

            # -----------------------------------
            # Supply Zone: high swing followed by bearish move
            # -----------------------------------
            elif swing_type == "high" and next_swing[2] == "low":
                zone_start = price
                zone_end = max(prev_swing[1], next_swing[1])
                zones.append(
                    SupplyDemandZone(
                        type="supply",
                        start_price=zone_start,
                        end_price=zone_end,
                        start_index=i,
                        end_index=i + 1,
                        timeframe=self.timeframe,
                    )
                )

        return zones
