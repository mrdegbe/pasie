from mtf.context_models import TopDownContext, TimeframeBias
from mtf.alignment import determine_overall_bias


class TopDownEngine:

    def __init__(self, structure_engine):
        self.structure_engine = structure_engine

    def analyze_symbol(self, symbol):

        weekly = self._build_tf(symbol, "W1")
        daily = self._build_tf(symbol, "D1")
        h4 = self._build_tf(symbol, "H4")

        overall = determine_overall_bias(weekly, daily, h4)

        return TopDownContext(
            overall_bias=overall,
            weekly=weekly,
            daily=daily,
            h4=h4,
            entry_timeframe="M15",
        )

    def _build_tf(self, symbol, timeframe):

        ctx = self.structure_engine.analyze(symbol, timeframe)

        structure_state = "range"

        if ctx.bos:
            structure_state = "continuation"

        return TimeframeBias(
            timeframe=timeframe,
            direction=ctx.direction,
            momentum_score=ctx.momentum_score,
            structure_state=structure_state,
            supply_zone=None,
            demand_zone=None,
            liquidity_zones=None,
            choch=None,
            imbalances=None,
        )


# liquidity_zones
# choch
# supply_zones
# demand_zones
# imbalances
