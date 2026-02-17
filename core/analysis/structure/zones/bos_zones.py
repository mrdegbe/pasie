# def detect_bos_zones(data, bos):

#     if not bos:
#         return []

#     zones = []

#     break_index = data.index.get_loc(bos["index"])

#     search_window = data.iloc[break_index - 10 : break_index]

#     if bos["type"] == "bullish_bos":

#         for i in reversed(range(len(search_window))):
#             candle = search_window.iloc[i]

#             if candle["Close"] < candle["Open"]:
#                 zones.append(
#                     {
#                         "type": "demand",
#                         "origin": "bos_origin",
#                         "proximal": candle["Open"],
#                         "distal": candle["Low"],
#                         "created_at": search_window.index[i],
#                     }
#                 )
#                 break

#     elif bos["type"] == "bearish_bos":

#         for i in reversed(range(len(search_window))):
#             candle = search_window.iloc[i]

#             if candle["Close"] > candle["Open"]:
#                 zones.append(
#                     {
#                         "type": "supply",
#                         "origin": "bos_origin",
#                         "proximal": candle["Open"],
#                         "distal": candle["High"],
#                         "created_at": search_window.index[i],
#                     }
#                 )
#                 break

#     return zones

from core.analysis.structure.zones.displacement import is_displacement_candle
from core.analysis.structure.zones.imbalances import has_imb


def detect_bos_zones(data, bos):

    if not bos:
        return []

    zones = []

    break_idx = data.index.get_loc(bos["index"])

    impulse_idx = break_idx - 1

    if impulse_idx < 2:
        return []

    # Validate displacement
    if not is_displacement_candle(data, impulse_idx):
        return []

    # Validate imbalance
    if not has_imb(data, impulse_idx):
        return []

    candle = data.iloc[impulse_idx]

    if bos["type"] == "bullish_bos":

        zones.append(
            {
                "type": "demand",
                "origin": "impulse_imbalance",
                "proximal": candle["High"],
                "distal": candle["Low"],
                "created_at": data.index[impulse_idx],
            }
        )

    elif bos["type"] == "bearish_bos":

        zones.append(
            {
                "type": "supply",
                "origin": "impulse_imbalance",
                "proximal": candle["Low"],
                "distal": candle["High"],
                "created_at": data.index[impulse_idx],
            }
        )

    return zones
