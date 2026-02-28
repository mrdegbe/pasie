from typing import Optional

from core.liquidity import LiquidityEngine
from core.models import Bias, StructureSnapshot
from core.utils import (
    calculate_momentum,
    compress_structure_after_bos,
    detect_bos,
    find_swings,
    get_bias,
    strict_alternation_structure,
)
from core.zones import SupplyDemandEngine


class StructureEngine:
    """
    Stateful multi-timeframe structure engine.

    Handles:
    - Swing detection
    - Break of Structure (BOS)
    - Bias memory
    - Pullback confirmation logic
    - Structural momentum
    """

    def __init__(
        self,
        symbol: str,
        internal_lookback: int = 3,
        external_lookback: int = 7,
        tolerance: float = 0.00005,
    ):
        self.symbol = symbol
        self.internal_lookback = internal_lookback
        self.external_lookback = external_lookback
        self.tolerance = tolerance

        # Persistent structure state
        self.bias: Optional[str] = None
        self.pending_bos: Optional[str] = None
        self.pending_level: Optional[float] = None
        self.awaiting_pullback: bool = False

    # ---------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------
    def analyze(self, data, timeframe: Optional[str] = None) -> StructureSnapshot:
        """
        Analyze market structure for provided OHLC data.
        """

        # ---------------------------------------------------
        # External (Macro) Structure
        # ---------------------------------------------------
        external_swings = strict_alternation_structure(
            self._build_external_structure(
                find_swings(data, self.external_lookback, self.tolerance)
            )
        )

        # external_swings = self._build_external_structure(raw_external_swings)

        structural_direction = get_bias(external_swings)

        # ---------------------------------------------------
        # Internal (Micro) Structure
        # ---------------------------------------------------
        internal_swings = strict_alternation_structure(
            find_swings(data, self.internal_lookback, self.tolerance)
        )

        internal_direction = get_bias(internal_swings)

        # ---------------------------------------------------
        # Detect BOS
        # ---------------------------------------------------
        bos = detect_bos(self.symbol, data, internal_swings)

        if bos:
            internal_swings = compress_structure_after_bos(internal_swings, bos)

        momentum = calculate_momentum(internal_swings)

        # ---------------------------------------------------
        # Initialize bias first time
        # ---------------------------------------------------
        if self.bias is None:
            self.bias = structural_direction

        # ---------------------------------------------------
        # Register BOS (Do not flip bias immediately)
        # ---------------------------------------------------
        if bos:
            self._handle_bos_registration(bos)

        # ---------------------------------------------------
        # Pullback Confirmation Logic
        # ---------------------------------------------------
        self._confirm_pullback(data, internal_direction)

        external_direction = self.bias

        # ---------------------------------------------------
        # Structural State Classification
        # ---------------------------------------------------
        state = self._classify_state(
            external_direction,
            internal_direction,
            bos,
        )

        current_price = data["Close"].iloc[-1]

        price_range = {
            "high": max(data["High"].iloc[-self.external_lookback :]),
            "low": min(data["Low"].iloc[-self.external_lookback :]),
        }

        # ---------------------------------------------------
        # Liquidity Detection
        # ---------------------------------------------------
        liquidity_engine = LiquidityEngine(
            timeframe=timeframe,
            tolerance=self.tolerance * 5,  # slightly wider for EQ clusters
        )
        liquidity_levels = liquidity_engine.detect(data)

        # -------------------------------
        # Supply/Demand Detection
        # -------------------------------
        sd_engine = SupplyDemandEngine(timeframe=timeframe)
        zones = sd_engine.detect_zones(data)

        return StructureSnapshot(
            symbol=self.symbol,
            timeframe=timeframe,
            bias=Bias(
                external=external_direction,
                internal=internal_direction,
            ),
            state=state,
            bos_event=bos,
            momentum=momentum,
            external_swings=external_swings,
            internal_swings=internal_swings,
            current_price=current_price,
            range=price_range,
            zones=zones,
            liquidity_levels=liquidity_levels,
        )

    # ---------------------------------------------------
    # INTERNAL STATE MANAGEMENT
    # ---------------------------------------------------
    def _handle_bos_registration(self, bos: dict) -> None:
        """
        Register BOS event but wait for pullback confirmation
        before flipping structural bias.
        """

        if self.awaiting_pullback:

            # Same direction BOS → strong continuation
            if bos["type"] == self.pending_bos:
                self.bias = "bullish" if "bullish" in bos["type"] else "bearish"
                self._reset_pending()

            # Opposite BOS → overwrite pending
            else:
                self.pending_bos = bos["type"]
                self.pending_level = bos["level"]
                self.awaiting_pullback = True

        else:
            self.pending_bos = bos["type"]
            self.pending_level = bos["level"]
            self.awaiting_pullback = True

    def _confirm_pullback(self, data, internal_direction: str) -> None:
        """
        Confirm pullback after BOS before flipping bias.
        """

        if not self.awaiting_pullback:
            return

        last_close = data["Close"].iloc[-2]

        # Bullish confirmation
        if (
            self.pending_bos == "bullish_bos"
            and internal_direction == "bearish"
            and last_close > self.pending_level
        ):
            self.bias = "bullish"
            self._reset_pending()

        # Bearish confirmation
        elif (
            self.pending_bos == "bearish_bos"
            and internal_direction == "bullish"
            and last_close < self.pending_level
        ):
            self.bias = "bearish"
            self._reset_pending()

    def _reset_pending(self) -> None:
        self.pending_bos = None
        self.pending_level = None
        self.awaiting_pullback = False

    # ---------------------------------------------------
    # STRUCTURAL STATE CLASSIFIER
    # ---------------------------------------------------
    def _classify_state(
        self,
        external_direction: str,
        internal_direction: str,
        bos: Optional[dict],
    ) -> str:

        if external_direction == "bullish":
            if bos and bos["type"] == "bullish_bos":
                return "bullish_expansion"
            if internal_direction == "bearish":
                return "bullish_correction"
            return "bullish_expansion"

        if external_direction == "bearish":
            if bos and bos["type"] == "bearish_bos":
                return "bearish_expansion"
            if internal_direction == "bullish":
                return "bearish_correction"
            return "bearish_expansion"

        if internal_direction != "neutral":
            return "transition"

        return "distribution"

    def _build_external_structure(self, swings):

        if len(swings) < 2:
            return swings

        external = []
        protected_high = None
        protected_low = None
        current_bias = None

        # 1️⃣ Initialize first structure leg
        external.append(swings[0])
        external.append(swings[1])

        if swings[0][2] == "low" and swings[1][2] == "high":
            current_bias = "bullish"
            protected_low = swings[0][1]
        else:
            current_bias = "bearish"
            protected_high = swings[0][1]

        # 2️⃣ Process remaining swings
        for swing in swings[2:]:

            time, price, swing_type = swing

            if current_bias == "bullish":

                # Only new HH expands structure
                if swing_type == "high" and price > external[-1][1]:
                    external.append(swing)
                    protected_low = external[-2][1]

                # Bearish break → structure shift
                elif swing_type == "low" and price < protected_low:
                    external.append(swing)
                    current_bias = "bearish"
                    protected_high = external[-2][1]

            elif current_bias == "bearish":

                # Only new LL expands structure
                if swing_type == "low" and price < external[-1][1]:
                    external.append(swing)
                    protected_high = external[-2][1]

                # Bullish break → structure shift
                elif swing_type == "high" and price > protected_high:
                    external.append(swing)
                    current_bias = "bullish"
                    protected_low = external[-2][1]

        return external
