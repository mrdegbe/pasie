# core/setup/evaluator.py

from typing import Optional, List
import pandas as pd

from core.models.analysis import TopDownSnapshot, StructureSnapshot
from core.models.setup import Setup


class SetupEvaluator:
    """
    Evaluates setups based on:
    - Top-down alignment
    - Structure (micro + macro)
    - Supply/Demand zones
    - Liquidity levels with sweep detection
    """

    def __init__(self, symbol: str):
        self.symbol = symbol

    def evaluate(
        self,
        topdown_snapshot: TopDownSnapshot,
        h4_snapshot: StructureSnapshot,
        m15_snapshot: StructureSnapshot,
        m15_df: pd.DataFrame,
    ) -> Optional[Setup]:
        """
        Evaluate the market and return a Setup object if valid.
        """

        # ---------------------------------------------------
        # 1️⃣ Macro / Top-down alignment
        # ---------------------------------------------------
        if not topdown_snapshot.is_aligned:
            return None  # Skip if macro not aligned

        macro_bias = topdown_snapshot.macro_bias  # 'bullish' or 'bearish'
        micro_bias = m15_snapshot.bias.external

        # Must align with macro
        if macro_bias != micro_bias:
            return None

        # ---------------------------------------------------
        # 2️⃣ Candidate SD zones in direction of bias
        # ---------------------------------------------------
        candidate_zones = [
            z
            for z in m15_snapshot.zones
            if (macro_bias == "bullish" and z.type == "demand")
            or (macro_bias == "bearish" and z.type == "supply")
        ]

        # ---------------------------------------------------
        # 3️⃣ Candidate liquidity levels (unswept)
        # ---------------------------------------------------
        candidate_levels = [
            l.price
            for l in m15_snapshot.liquidity_levels
            if (
                macro_bias == "bullish"
                and l.liquidity_type in ["swing_low", "equal_low"]
                and not l.swept
            )
            or (
                macro_bias == "bearish"
                and l.liquidity_type in ["swing_high", "equal_high"]
                and not l.swept
            )
        ]

        # ---------------------------------------------------
        # 4️⃣ Determine entry
        # ---------------------------------------------------
        if candidate_levels:
            # Take closest liquidity cluster as entry
            entry = (
                min(candidate_levels)
                if macro_bias == "bullish"
                else max(candidate_levels)
            )
        elif candidate_zones:
            # Fallback: zone midpoint
            entry = sum(
                [(z.start_price + z.end_price) / 2 for z in candidate_zones]
            ) / len(candidate_zones)
        else:
            return None  # No confluence → skip

        # ---------------------------------------------------
        # 5️⃣ Calculate ATR for SL/TP sizing
        # ---------------------------------------------------
        atr = self._calculate_atr(m15_df, period=14)
        sl_distance = atr * 1.5
        tp_distance = atr * 3

        # SL / TP placement
        if macro_bias == "bullish":
            stop_loss = (
                min([z.start_price for z in candidate_zones] + [entry - sl_distance])
                if candidate_zones
                else entry - sl_distance
            )
            take_profit = max(
                [l.price for l in m15_snapshot.liquidity_levels if l.price > entry]
                + [entry + tp_distance]
            )
        else:
            stop_loss = (
                max([z.start_price for z in candidate_zones] + [entry + sl_distance])
                if candidate_zones
                else entry + sl_distance
            )
            take_profit = min(
                [l.price for l in m15_snapshot.liquidity_levels if l.price < entry]
                + [entry - tp_distance]
            )

        # ---------------------------------------------------
        # 6️⃣ Confidence scoring
        # ---------------------------------------------------
        confidence_score = (
            topdown_snapshot.alignment_score * 0.4  # macro alignment
            + (1 if micro_bias == macro_bias else 0) * 0.3  # micro alignment
            + min(len(candidate_zones), 3) / 3 * 0.2  # SD zone confluence
            + min(len(candidate_levels), 3) / 3 * 0.1  # liquidity confluence
        )

        # ---------------------------------------------------
        # 7️⃣ Return Setup
        # ---------------------------------------------------
        return Setup(
            symbol=self.symbol,
            direction=macro_bias,
            entry=float(entry),
            stop_loss=float(stop_loss),
            take_profit=float(take_profit),
            risk_reward=float((take_profit - entry) / abs(stop_loss - entry)),
            confidence_score=float(confidence_score),
        )

    # ---------------------------------------------------
    # HELPER METHODS
    # ---------------------------------------------------
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Simple ATR calculation using High-Low.
        """
        high = df["High"]
        low = df["Low"]

        tr = (high - low).to_list()
        if len(tr) < period:
            return sum(tr) / len(tr)
        return sum(tr[-period:]) / period
