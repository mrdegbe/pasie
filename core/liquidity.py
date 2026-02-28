from core.models import LiquidityLevel


class LiquidityEngine:

    def __init__(self, timeframe: str, tolerance: float = 0.0002):
        """
        tolerance = price tolerance to consider highs/lows equal
        """
        self.timeframe = timeframe
        self.tolerance = tolerance

    def detect(self, df):
        swing_levels = self._detect_swings(df)
        eq_levels = self._detect_equal_levels(df)

        all_levels = swing_levels + eq_levels
        all_levels = self.detect_sweeps(df, all_levels)

        # DEBUGGING
        # print("Total levels:", len(all_levels))
        # print("Swept levels:", sum(1 for l in all_levels if l.swept))

        return all_levels

    def detect_sweeps(self, df, liquidity_levels):
        highs = df["High"].values
        lows = df["Low"].values

        for level in liquidity_levels:

            if level.swept:
                continue

            # 🔥 Only check candles AFTER liquidity formation
            formation_index = max(level.indices)
            start_index = formation_index + 1

            for i in range(start_index, len(df)):

                # Buy-side liquidity
                if level.liquidity_type in ["swing_high", "equal_high"]:
                    if highs[i] > level.price + self.tolerance:
                        level.swept = True
                        level.swept_at_index = i
                        break

                # Sell-side liquidity
                elif level.liquidity_type in ["swing_low", "equal_low"]:
                    if lows[i] < level.price - self.tolerance:
                        level.swept = True
                        level.swept_at_index = i
                        break

        return liquidity_levels

    # --------------------------------------------------
    # 1️⃣ Swing High / Low
    # --------------------------------------------------

    def _detect_swings(self, df):
        levels = []

        highs = df["High"].values
        lows = df["Low"].values

        for i in range(2, len(df) - 2):

            # Swing High
            if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
                levels.append(
                    LiquidityLevel(
                        price=highs[i],
                        liquidity_type="swing_high",
                        timeframe=self.timeframe,
                        indices=[i],
                    )
                )

            # Swing Low
            if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
                levels.append(
                    LiquidityLevel(
                        price=lows[i],
                        liquidity_type="swing_low",
                        timeframe=self.timeframe,
                        indices=[i],
                    )
                )

        return levels

    # --------------------------------------------------
    # 2️⃣ Equal High / Equal Low Clusters
    # --------------------------------------------------

    def _detect_equal_levels(self, df):
        levels = []

        highs = df["High"].values
        lows = df["Low"].values

        # Equal High Detection
        levels += self._cluster_equal_prices(highs, "equal_high")

        # Equal Low Detection
        levels += self._cluster_equal_prices(lows, "equal_low")

        return levels

    def _cluster_equal_prices(self, prices, liquidity_type):
        clusters = []
        visited = set()

        for i in range(len(prices)):
            if i in visited:
                continue

            cluster_indices = [i]

            for j in range(i + 1, len(prices)):
                if abs(prices[i] - prices[j]) <= self.tolerance:
                    cluster_indices.append(j)
                    visited.add(j)

            if len(cluster_indices) >= 2:
                avg_price = sum(prices[k] for k in cluster_indices) / len(
                    cluster_indices
                )

                clusters.append(
                    LiquidityLevel(
                        price=avg_price,
                        liquidity_type=liquidity_type,
                        timeframe=self.timeframe,
                        indices=cluster_indices,
                    )
                )

        return clusters
