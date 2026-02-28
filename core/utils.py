import MetaTrader5 as mt5
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)
Swing = Tuple  # (timestamp, price, type)

# Pip size helper function
# def get_pip_size(symbol):
#     if "JPY" in symbol:
#         return 0.01
#     return 0.0001


def get_pip_size(symbol: str) -> float:
    info = mt5.symbol_info(symbol)
    if info is None:
        raise ValueError(f"Symbol info not found for {symbol}")

    digits = info.digits

    # Forex logic
    if digits == 5:
        return 0.0001
    elif digits == 3:
        return 0.01
    elif digits == 2:
        return 0.1
    else:
        return 10 ** (-digits)


# ---------------------------------------------
# BIAS DETERMINATION USING SEQUENTIAL SWING LOGIC
# ---------------------------------------------
def get_bias(swings: List[Swing], tolerance: float = 0.0) -> str:
    """
    Determine market structural direction using sequential swing logic.

    Parameters
    ----------
    swings : List[Tuple]
        List of swings formatted as (timestamp, price, type),
        where type is either "high" or "low".

    tolerance : float
        Allowed tolerance when comparing swing prices.
        Helps ignore tiny price differences caused by noise.

    Returns
    -------
    str
        "bullish", "bearish", or "neutral"
    """

    if len(swings) < 4:
        logger.debug("Not enough swings to determine direction.")
        return "neutral"

    # Extract last 4 swings (latest structural cycle)
    s1, s2, s3, s4 = swings[-4:]

    logger.debug("Evaluating swings: %s", [s1, s2, s3, s4])

    # -----------------------------------------
    # Pattern: High → Low → High → Low
    # -----------------------------------------
    if s1[2] == "high" and s2[2] == "low" and s3[2] == "high" and s4[2] == "low":

        prev_high, prev_low = s1[1], s2[1]
        last_high, last_low = s3[1], s4[1]

        if last_high > prev_high * (1 - tolerance) and last_low > prev_low * (
            1 - tolerance
        ):
            logger.info("Structure identified as BULLISH.")
            return "bullish"

        if last_high < prev_high * (1 + tolerance) and last_low < prev_low * (
            1 + tolerance
        ):
            logger.info("Structure identified as BEARISH.")
            return "bearish"

    # -----------------------------------------
    # Pattern: Low → High → Low → High
    # -----------------------------------------
    elif s1[2] == "low" and s2[2] == "high" and s3[2] == "low" and s4[2] == "high":

        prev_low, prev_high = s1[1], s2[1]
        last_low, last_high = s3[1], s4[1]

        if last_high > prev_high * (1 - tolerance) and last_low > prev_low * (
            1 - tolerance
        ):
            logger.info("Structure identified as BULLISH.")
            return "bullish"

        if last_high < prev_high * (1 + tolerance) and last_low < prev_low * (
            1 + tolerance
        ):
            logger.info("Structure identified as BEARISH.")
            return "bearish"

    logger.debug("No clear structure detected.")
    return "neutral"


# ------------------------------------------------
# REFINED BOS DETECTION (DISPLACEMENT REQUIRED)
# ------------------------------------------------
def detect_bos(
    symbol,
    data,
    swings,
    pip_buffer=2,
    displacement_multiplier=1.5,
    body_threshold=0.6,
    lookback=20,
):
    """
    Detect Break of Structure (BOS) using confirmed closed candles
    and displacement validation.
    """

    # ---------------------------------------------------
    # Guard Clauses
    # ---------------------------------------------------
    if len(swings) < 2:
        return None

    if len(data) < lookback + 2:
        return None

    # ---------------------------------------------------
    # Separate swing highs and lows
    # ---------------------------------------------------
    swing_highs = [s for s in swings if s[2] == "high"]
    swing_lows = [s for s in swings if s[2] == "low"]

    if not swing_highs or not swing_lows:
        return None

    last_high = swing_highs[-1]
    last_low = swing_lows[-1]

    # ---------------------------------------------------
    # Pip Buffer (prevents false micro breaks)
    # ---------------------------------------------------
    pip_value = get_pip_size(symbol)
    buffer = pip_buffer * pip_value

    # ---------------------------------------------------
    # Use Last CONFIRMED Closed Candle
    # ---------------------------------------------------
    candle = data.iloc[-2]

    current_open = candle["Open"]
    current_close = candle["Close"]
    current_high = candle["High"]
    current_low = candle["Low"]

    # ---------------------------------------------------
    # Displacement Calculation
    # ---------------------------------------------------
    current_range = current_high - current_low

    historical_ranges = (data["High"] - data["Low"]).iloc[-lookback - 1 : -2]
    avg_range = historical_ranges.mean()

    if avg_range == 0:
        return None

    body = abs(current_close - current_open)
    body_percent = body / current_range if current_range != 0 else 0

    displacement_confirmed = (
        current_range > displacement_multiplier * avg_range
        and body_percent > body_threshold
    )

    # ---------------------------------------------------
    # Bullish BOS Detection
    # ---------------------------------------------------
    if (
        current_close > last_high[1] + buffer
        and displacement_confirmed
        and current_close > current_open
    ):
        return {
            "type": "bullish_bos",
            "level": last_high[1],
            "break_price": current_close,
            "index": data.index[-2],
        }

    # ---------------------------------------------------
    # Bearish BOS Detection
    # ---------------------------------------------------
    if (
        current_close < last_low[1] - buffer
        and displacement_confirmed
        and current_close < current_open
    ):
        return {
            "type": "bearish_bos",
            "level": last_low[1],
            "break_price": current_close,
            "index": data.index[-2],
        }

    return None


# --------------------------------------------
# STRUCTURE COMPRESSION
# --------------------------------------------
def compress_structure_after_bos(swings, bos):
    """
    Compress swing structure after confirmed BOS.

    Keeps:
    - The protected swing level (last opposite swing before BOS)
    - The newest swing that confirms the new structure
    """

    # ---------------------------------------------------
    # Guard Clauses
    # ---------------------------------------------------
    if bos is None or len(swings) < 2:
        return swings

    bos_level = bos["level"]
    bos_type = bos["type"]

    # ---------------------------------------------------
    # Locate the swing level that was broken
    # ---------------------------------------------------
    broken_index = next(
        (i for i, s in enumerate(swings) if abs(s[1] - bos_level) < 1e-10),
        None,
    )

    if broken_index is None:
        return swings

    # ---------------------------------------------------
    # Bullish BOS → find last LOW before broken HIGH
    # ---------------------------------------------------
    if bos_type == "bullish_bos":
        for i in range(broken_index - 1, -1, -1):
            if swings[i][2] == "low":
                return [swings[i], swings[-1]]

    # ---------------------------------------------------
    # Bearish BOS → find last HIGH before broken LOW
    # ---------------------------------------------------
    if bos_type == "bearish_bos":
        for i in range(broken_index - 1, -1, -1):
            if swings[i][2] == "high":
                return [swings[i], swings[-1]]

    return swings


# ------------------------------
# STRUCTURAL MOMENTUM
# ------------------------------
def calculate_momentum(swings):
    """
    Calculate structural momentum score based on progression
    of recent swing highs and lows.

    Returns:
        int: Momentum score
             +2 = strong bullish momentum
             +1 = bullish momentum
              0 = neutral / mixed
             -1 = bearish momentum
             -2 = strong bearish momentum
    """

    # ---------------------------------------------------
    # Extract swing highs and lows
    # ---------------------------------------------------
    highs = [price for _, price, t in swings if t == "high"]
    lows = [price for _, price, t in swings if t == "low"]

    score = 0

    # ---------------------------------------------------
    # Higher Highs → Bullish Strength
    # ---------------------------------------------------
    if len(highs) >= 3:
        if highs[-3] < highs[-2] < highs[-1]:
            score += 1

    # ---------------------------------------------------
    # Higher Lows → Bullish Strength
    # ---------------------------------------------------
    if len(lows) >= 3:
        if lows[-3] < lows[-2] < lows[-1]:
            score += 1

    # ---------------------------------------------------
    # Lower Highs → Bearish Strength
    # ---------------------------------------------------
    if len(highs) >= 3:
        if highs[-3] > highs[-2] > highs[-1]:
            score -= 1

    # ---------------------------------------------------
    # Lower Lows → Bearish Strength
    # ---------------------------------------------------
    if len(lows) >= 3:
        if lows[-3] > lows[-2] > lows[-1]:
            score -= 1

    return score


# ===================================================
# 1️⃣ SWING DETECTION
# ===================================================
def find_swings(data, lookback: int = 3, tolerance: float = 0.0):
    """
    Detect swing highs and swing lows using symmetric lookback confirmation.

    Args:
        data: OHLC dataframe with 'High' and 'Low' columns
        lookback: Number of candles to check on each side
        tolerance: Percentage tolerance for near-equal highs/lows

    Returns:
        List of tuples:
        (timestamp, price, 'high' or 'low')
    """

    swings = []

    highs = data["High"]
    lows = data["Low"]
    index = data.index

    for i in range(lookback, len(data) - lookback):

        current_high = highs.iloc[i]
        current_low = lows.iloc[i]

        left_highs = highs.iloc[i - lookback : i]
        right_highs = highs.iloc[i + 1 : i + lookback + 1]

        left_lows = lows.iloc[i - lookback : i]
        right_lows = lows.iloc[i + 1 : i + lookback + 1]

        is_swing_high = all(
            current_high >= h * (1 - tolerance) for h in left_highs
        ) and all(current_high >= h * (1 - tolerance) for h in right_highs)

        is_swing_low = all(
            current_low <= l * (1 + tolerance) for l in left_lows
        ) and all(current_low <= l * (1 + tolerance) for l in right_lows)

        if is_swing_high:
            swings.append((index[i], current_high, "high"))

        if is_swing_low:
            swings.append((index[i], current_low, "low"))

    return swings


# ===================================================
# 2️⃣ STRICT FRACTAL ALTERNATION
# ===================================================
def strict_alternation_structure(swings):
    """
    Enforce strict alternation between swing highs and lows.

    Removes consecutive swings of the same type by keeping
    only the most extreme one.

    Args:
        swings: List of tuples -> (timestamp, price, type)

    Returns:
        Cleaned list of alternating swings.
    """

    if not swings:
        return []

    cleaned = [swings[0]]

    for swing in swings[1:]:
        last = cleaned[-1]

        swing_time, swing_price, swing_type = swing
        _, last_price, last_type = last

        # If swing type alternates → valid structure
        if swing_type != last_type:
            cleaned.append(swing)
            continue

        # Same type → keep the more extreme swing
        if swing_type == "low" and swing_price < last_price:
            cleaned[-1] = swing

        elif swing_type == "high" and swing_price > last_price:
            cleaned[-1] = swing

    return cleaned
