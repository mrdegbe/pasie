# def detect_base_zones(data, lookback=20, base_threshold=0.5):

#     zones = []

#     ranges = data["High"] - data["Low"]
#     avg_range = ranges.rolling(lookback).mean()

#     for i in range(lookback, len(data) - 2):

#         if ranges.iloc[i] < avg_range.iloc[i] * base_threshold:

#             # check surrounding impulse
#             prev = data.iloc[i - 1]
#             next_candle = data.iloc[i + 1]

#             # Rally Base Rally
#             if (
#                 prev["Close"] > prev["Open"]
#                 and next_candle["Close"] > next_candle["Open"]
#             ):

#                 zones.append(
#                     {
#                         "type": "demand",
#                         "origin": "base_pattern",
#                         "proximal": data["Open"].iloc[i],
#                         "distal": data["Low"].iloc[i],
#                         "created_at": data.index[i],
#                     }
#                 )

#             # Drop Base Drop
#             if (
#                 prev["Close"] < prev["Open"]
#                 and next_candle["Close"] < next_candle["Open"]
#             ):

#                 zones.append(
#                     {
#                         "type": "supply",
#                         "origin": "base_pattern",
#                         "proximal": data["Open"].iloc[i],
#                         "distal": data["High"].iloc[i],
#                         "created_at": data.index[i],
#                     }
#                 )

#     return zones


from core.analysis.structure.zones.displacement import is_displacement_candle
from core.analysis.structure.zones.imbalances import detect_imbalance
from core.analysis.structure.zones.zones import build_zone_from_base


def detect_base_zones(data):
    """
    Detect zones using:
    Base candle BEFORE displacement + imbalance.
    """

    demand_zones = []
    supply_zones = []

    for i in range(len(data)):

        imbalance = detect_imbalance(data, i)

        if not imbalance:
            continue

        if not is_displacement_candle(data, i):
            continue

        base_index = i - 1

        if base_index < 0:
            continue

        # Determine zone direction
        if imbalance["type"] == "bullish":
            zone = build_zone_from_base(data, base_index, "demand")
            demand_zones.append(zone)

        else:
            zone = build_zone_from_base(data, base_index, "supply")
            supply_zones.append(zone)

    return demand_zones + supply_zones
