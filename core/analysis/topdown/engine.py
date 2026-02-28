from typing import Dict

from core.analysis.structure.engine import StructureEngine
from core.models.analysis import TopDownSnapshot


class TopDownEngine:
    """
    Multi-timeframe orchestration engine.

    Handles:
    - Structure alignment across W1, D1, H4, M15
    - Weighted scoring
    - Macro bias determination
    """

    WEIGHTS = {
        "W1": 40,
        "D1": 30,
        "H4": 20,
        "M15": 10,
    }

    def __init__(self, symbol: str):
        self.symbol = symbol

        self.engines = {
            "W1": StructureEngine(symbol),
            "D1": StructureEngine(symbol),
            "H4": StructureEngine(symbol),
            "M15": StructureEngine(symbol),
        }

    # ---------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------
    def analyze(self, data_map: Dict[str, object]) -> TopDownSnapshot:
        """
        data_map:
            {
                "W1": dataframe,
                "D1": dataframe,
                "H4": dataframe,
                "M15": dataframe
            }
        """

        snapshots = {}
        total_score = 0
        bias_score = {"bullish": 0, "bearish": 0}

        for tf, engine in self.engines.items():
            snapshot = engine.analyze(data_map[tf], timeframe=tf)
            snapshots[tf] = snapshot

            tf_score = self._score_timeframe(snapshot, tf)
            total_score += tf_score

            if snapshot.bias.external in bias_score:
                bias_score[snapshot.bias.external] += self.WEIGHTS[tf]

        macro_bias = self._determine_macro_bias(bias_score)

        alignment_score = max(bias_score.values())
        is_aligned = alignment_score >= 70  # threshold for strong alignment

        return TopDownSnapshot(
            symbol=self.symbol,
            macro_bias=macro_bias,
            alignment_score=alignment_score,
            total_score=total_score,
            is_aligned=is_aligned,
            timeframe_snapshots=snapshots,
        )

    # ---------------------------------------------------
    # SCORING LOGIC
    # ---------------------------------------------------
    def _score_timeframe(self, snapshot, timeframe: str) -> int:

        weight = self.WEIGHTS[timeframe]
        score = 0

        # Structural bias contributes full weight
        if snapshot.bias.external in ["bullish", "bearish"]:
            score += weight

        # Momentum bonus (max 5 extra points)
        score += max(min(snapshot.momentum, 2), -2) * 2

        # Expansion bonus
        if "expansion" in snapshot.state:
            score += 3

        return score

    # ---------------------------------------------------
    # MACRO BIAS DECISION
    # ---------------------------------------------------
    def _determine_macro_bias(self, bias_score: Dict[str, int]) -> str:

        if bias_score["bullish"] > bias_score["bearish"]:
            return "bullish"

        if bias_score["bearish"] > bias_score["bullish"]:
            return "bearish"

        return "neutral"
