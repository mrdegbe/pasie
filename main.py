import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf


# -----------------------------
# 1. Connect to MT5
# -----------------------------
if not mt5.initialize():
    print("Initialization failed:", mt5.last_error())
    quit()

print("MT5 connected")

symbol = "GBPJPYm"

if not mt5.symbol_select(symbol, True):
    print("Failed to select symbol")
    mt5.shutdown()
    quit()

# -----------------------------
# Fetch M15 Data (Execution TF)
# -----------------------------

rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 300)

if rates_m15 is None:
    print("Failed to get M15 rates:", mt5.last_error())
    mt5.shutdown()
    quit()

df_m15 = pd.DataFrame(rates_m15)
df_m15['time'] = pd.to_datetime(df_m15['time'], unit='s')
df_m15.set_index('time', inplace=True)

# -----------------------------
# Fetch H4 Data (Bias TF)
# -----------------------------

rates_h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 300)

if rates_h4 is None:
    print("Failed to get H4 rates:", mt5.last_error())
    mt5.shutdown()
    quit()

df_h4 = pd.DataFrame(rates_h4)
df_h4['time'] = pd.to_datetime(df_h4['time'], unit='s')
df_h4.set_index('time', inplace=True)


# -----------------------------
# Data Formatting
# -----------------------------
def format_dataframe(df):
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'tick_volume': 'Volume'
    }, inplace=True)
    return df

df_m15 = format_dataframe(df_m15)
df_h4 = format_dataframe(df_h4)



# -----------------------------
# 2. Structure Logic (Swings)
# -----------------------------

def find_swings(data, lookback=3):
    swings = []

    for i in range(lookback, len(data) - lookback):
        high = data['High'].iloc[i]
        low = data['Low'].iloc[i]

        is_swing_high = all(high > data['High'].iloc[i - j] for j in range(1, lookback + 1)) and \
                        all(high > data['High'].iloc[i + j] for j in range(1, lookback + 1))

        is_swing_low = all(low < data['Low'].iloc[i - j] for j in range(1, lookback + 1)) and \
                       all(low < data['Low'].iloc[i + j] for j in range(1, lookback + 1))

        if is_swing_high:
            swings.append((data.index[i], high, "high"))

        if is_swing_low:
            swings.append((data.index[i], low, "low"))

    return swings

# -----------------------------
# 4. Determine market structure
# -----------------------------

def determine_structure(swings):
    highs = [s for s in swings if s[2] == "high"]
    lows = [s for s in swings if s[2] == "low"]

    if len(highs) < 2 or len(lows) < 2:
        return "neutral"

    last_high, prev_high = highs[-1], highs[-2]
    last_low, prev_low = lows[-1], lows[-2]

    if last_high[1] > prev_high[1] and last_low[1] > prev_low[1]:
        return "bullish"

    if last_high[1] < prev_high[1] and last_low[1] < prev_low[1]:
        return "bearish"

    return "neutral"


# structure = determine_structure(swings)
# print("Current structure:", structure.upper())

# --- 15M ---
swings_m15 = find_swings(df_m15)
structure_m15 = determine_structure(swings_m15)

# --- H4 ---
swings_h4 = find_swings(df_h4)
structure_h4 = determine_structure(swings_h4)

print("4H Bias:", structure_h4.upper())
print("15M Structure:", structure_m15.upper())


# -----------------------------
# 5. Detect Break of Structure
# -----------------------------

def detect_bos(data, swings, structure):
    if not swings:
        return None

    highs = [s for s in swings if s[2] == "high"]
    lows = [s for s in swings if s[2] == "low"]

    if structure == "bullish" and highs:
        last_swing_high = highs[-1][1]
        current_close = data['Close'].iloc[-1]

        if current_close > last_swing_high:
            return "bullish_bos"

    if structure == "bearish" and lows:
        last_swing_low = lows[-1][1]
        current_close = data['Close'].iloc[-1]

        if current_close < last_swing_low:
            return "bearish_bos"

    return None


# -----------------------------
# 6. Detect CHoCH
# -----------------------------

def detect_choch(data, swings, structure,
                 range_multiplier=1.5,
                 volume_multiplier=1.5,
                 lookback=20):

    if len(data) < lookback + 1:
        return None, None

    highs = [s for s in swings if s[2] == "high"]
    lows = [s for s in swings if s[2] == "low"]

    current_close = data['Close'].iloc[-1]
    current_high = data['High'].iloc[-1]
    current_low = data['Low'].iloc[-1]
    current_open = data['Open'].iloc[-1]
    current_volume = data['Volume'].iloc[-1]

    # --- Displacement calculation ---
    current_range = current_high - current_low
    avg_range = (data['High'] - data['Low']).iloc[-lookback:-1].mean()

    body_size = abs(current_close - current_open)
    body_percent = body_size / current_range if current_range != 0 else 0

    displacement = (
        current_range > range_multiplier * avg_range and
        body_percent > 0.6
    )

    # --- Volume expansion ---
    avg_volume = data['Volume'].iloc[-lookback:-1].mean()
    volume_expansion = current_volume > volume_multiplier * avg_volume

    # --- CHoCH logic ---
    reasons = []

    if structure == "bearish" and highs:
        last_lower_high = highs[-1][1]

        if current_close > last_lower_high:
            reasons.append("Closed above last lower high")

            if displacement:
                reasons.append("Displacement confirmed")

            if volume_expansion:
                reasons.append("Volume expansion confirmed")

            if displacement and volume_expansion:
                return "bullish_choch", reasons

    if structure == "bullish" and lows:
        last_higher_low = lows[-1][1]

        if current_close < last_higher_low:
            reasons.append("Closed below last higher low")

            if displacement:
                reasons.append("Displacement confirmed")

            if volume_expansion:
                reasons.append("Volume expansion confirmed")

            if displacement and volume_expansion:
                return "bearish_choch", reasons

    return None, None

bos_signal = detect_bos(df_m15, swings_m15, structure_m15)

if bos_signal:
    print("BOS DETECTED:", bos_signal.upper())
else:
    print("No BOS detected")

# choch_signal, choch_reasons = detect_choch(df_m15, swings_m15, structure_m15)

# if choch_signal:
#     print("\nCHOCH DETECTED:", choch_signal.upper())
#     print("Reasons:")
#     for r in choch_reasons:
#         print("-", r)
# else:
#     print("No CHoCH detected")

choch_signal, choch_reasons = detect_choch(df_m15, swings_m15, structure_m15)

valid_signal = None

if choch_signal:
    if structure_h4 == "bullish" and choch_signal == "bullish_choch":
        valid_signal = "A-Grade Bullish Setup"

    elif structure_h4 == "bearish" and choch_signal == "bearish_choch":
        valid_signal = "A-Grade Bearish Setup"

    else:
        valid_signal = "Counter-trend (B-Grade)"

if valid_signal:
    print("\nSETUP DETECTED:", valid_signal)

    if choch_reasons:
        print("Reasons:")
        for r in choch_reasons:
            print("-", r)
else:
    print("No valid HTF-aligned CHoCH")


# -----------------------------
# 3. Plot Candlestick Chart
# -----------------------------

import numpy as np

# Create empty series full of NaN
swing_highs = pd.Series(np.nan, index=df_m15.index)
swing_lows = pd.Series(np.nan, index=df_m15.index)

# Populate swing points
for swing in swings_m15:
    time, price, swing_type = swing
    if swing_type == "high":
        swing_highs.loc[time] = price
    else:
        swing_lows.loc[time] = price

apds = [
    mpf.make_addplot(swing_highs, type='scatter', marker='v', markersize=100),
    mpf.make_addplot(swing_lows, type='scatter', marker='^', markersize=100)
]

mpf.plot(
    df_m15,
    type='candle',
    addplot=apds,
    title=f"{symbol} M15 Structure ({structure_m15.upper()})",
    style='charles',
    volume=False
)



# -----------------------------
# 3. Plot Candlestick Chart
# -----------------------------

# Prepare swing markers
# highs_x = []
# highs_y = []
# lows_x = []
# lows_y = []

# for swing in swings:
#     if swing[2] == "high":
#         highs_x.append(swing[0])
#         highs_y.append(swing[1])
#     else:
#         lows_x.append(swing[0])
#         lows_y.append(swing[1])

# apds = []

# if highs_x:
#     apds.append(mpf.make_addplot(
#         pd.Series(highs_y, index=highs_x),
#         type='scatter',
#         marker='v',
#         markersize=100
#     ))

# if lows_x:
#     apds.append(mpf.make_addplot(
#         pd.Series(lows_y, index=lows_x),
#         type='scatter',
#         marker='^',
#         markersize=100
#     ))

# mpf.plot(
#     df,
#     type='candle',
#     addplot=apds,
#     title=f"{symbol} M15 Structure ({structure.upper()})",
#     style='charles',
#     volume=False
# )



# -----------------------------
# 3. Plot
# -----------------------------
# plt.figure(figsize=(12, 6))
# plt.plot(df['time'], df['close'])

# for swing in swings:
#     if swing[2] == "high":
#         plt.scatter(swing[0], swing[1])
#     else:
#         plt.scatter(swing[0], swing[1])

# plt.title("Live EURUSD M15 Structure")
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.show()

# mt5.shutdown()


