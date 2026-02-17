from structure.bos import detect_bos
from structure.momentum import calculate_momentum


def evaluate_timeframe(symbol, timeframe, data, swings):

    bos = detect_bos(symbol, data, swings)
    momentum = calculate_momentum(swings)

    direction = "neutral"
    structure_state = "range"

    if bos:
        if "bullish" in bos["type"]:
            direction = "bullish"
            structure_state = "continuation"
        else:
            direction = "bearish"
            structure_state = "continuation"

    return {
        "direction": direction,
        "momentum": momentum,
        "structure_state": structure_state,
        "bos": bos,
    }
