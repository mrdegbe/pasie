# utils/structure.py

import numpy as np
from utils.bias import get_direction
from utils.helper import get_pip_size


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


# # ===================================================
# 3️⃣ SEQUENTIAL STRUCTURE DIRECTION
# # ===================================================


# ===================================================
# 4️⃣ REFINED BOS DETECTION (DISPLACEMENT REQUIRED)
# ===================================================
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


# ===================================================
# 5️⃣ STRUCTURAL MOMENTUM
# ===================================================
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


# ===================================================
# 6️⃣ MASTER STRUCTURE ENGINE (MULTI-PAIR SAFE)
# ===================================================
def analyze_structure(
    data,
    internal_lookback: int = 3,
    external_lookback: int = 7,
    tolerance: float = 0.00005,
    symbol: str | None = None,
):
    """
    Multi-pair market structure analyzer.
    Maintains persistent structural bias per symbol.
    """

    # ---------------------------------------------------
    # Validate symbol (required for multi-pair state)
    # ---------------------------------------------------
    if symbol is None:
        raise ValueError("Symbol must be provided for multi-pair structure tracking.")

    # ---------------------------------------------------
    # Initialize persistent state container
    # ---------------------------------------------------
    if not hasattr(analyze_structure, "_state"):
        analyze_structure._state = {}

    # Create symbol state if not existing
    if symbol not in analyze_structure._state:
        analyze_structure._state[symbol] = {
            "bias": None,
            "pending_bos": None,
            "pending_level": None,
            "awaiting_pullback": False,
        }

    state_memory = analyze_structure._state[symbol]

    # ---------------------------------------------------
    # External (macro) structure
    # ---------------------------------------------------
    external_swings = strict_alternation_structure(
        find_swings(data, external_lookback, tolerance)
    )

    # ---------------------------------------------------
    # Internal (micro) structure
    # ---------------------------------------------------
    internal_swings = strict_alternation_structure(
        find_swings(data, internal_lookback, tolerance)
    )

    internal_direction = get_direction(internal_swings)

    # ---------------------------------------------------
    # Detect Break of Structure (BOS)
    # ---------------------------------------------------
    bos = detect_bos(symbol, data, internal_swings)

    if bos:
        internal_swings = compress_structure_after_bos(internal_swings, bos)

    momentum = calculate_momentum(internal_swings)

    # ---------------------------------------------------
    # Structural baseline direction
    # ---------------------------------------------------
    structural_direction = get_direction(external_swings)

    # Initialize bias first time only
    if state_memory["bias"] is None:
        state_memory["bias"] = structural_direction

    # ---------------------------------------------------
    # Register BOS (but do not flip bias yet)
    # ---------------------------------------------------
    if bos:
        state_memory.update(
            {
                "pending_bos": bos["type"],
                "pending_level": bos["level"],
                "awaiting_pullback": True,
            }
        )

    # ---------------------------------------------------
    # Pullback confirmation logic
    # ---------------------------------------------------
    if state_memory["awaiting_pullback"]:

        last_close = data["Close"].iloc[-2]
        pending_type = state_memory["pending_bos"]
        pending_level = state_memory["pending_level"]

        # Bullish confirmation
        if (
            pending_type == "bullish_bos"
            and internal_direction == "bearish"
            and last_close > pending_level
        ):
            state_memory.update(
                {
                    "bias": "bullish",
                    "pending_bos": None,
                    "pending_level": None,
                    "awaiting_pullback": False,
                }
            )

        # Bearish confirmation
        elif (
            pending_type == "bearish_bos"
            and internal_direction == "bullish"
            and last_close < pending_level
        ):
            state_memory.update(
                {
                    "bias": "bearish",
                    "pending_bos": None,
                    "pending_level": None,
                    "awaiting_pullback": False,
                }
            )

    external_direction = state_memory["bias"]

    # ---------------------------------------------------
    # Structural state classification
    # ---------------------------------------------------
    state = "distribution"

    if external_direction == "bullish":
        if bos and bos["type"] == "bullish_bos":
            state = "bullish_expansion"
        elif internal_direction == "bearish":
            state = "bullish_correction"
        else:
            state = "bullish_expansion"

    elif external_direction == "bearish":
        if bos and bos["type"] == "bearish_bos":
            state = "bearish_expansion"
        elif internal_direction == "bullish":
            state = "bearish_correction"
        else:
            state = "bearish_expansion"

    else:
        state = "transition" if internal_direction != "neutral" else "distribution"

    return {
        "symbol": symbol,
        "external_direction": external_direction,
        "internal_direction": internal_direction,
        "state": state,
        "bos": bos,
        "momentum_score": momentum,
        "external_swings": external_swings,
        "internal_swings": internal_swings,
    }
