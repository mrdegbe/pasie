import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# 1. Connect to MT5
# -----------------------------
if not mt5.initialize():
    print("Initialization failed:", mt5.last_error())
    quit()

print("MT5 connected")

symbol = "EURUSD"

if not mt5.symbol_select(symbol, True):
    print("Failed to select symbol")
    mt5.shutdown()
    quit()

# Get 300 candles for better structure visibility
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 300)

if rates is None:
    print("Failed to get rates:", mt5.last_error())
    mt5.shutdown()
    quit()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')


# -----------------------------
# 2. Structure Logic (Swings)
# -----------------------------
def find_swings(data, lookback=3):
    swings = []

    for i in range(lookback, len(data) - lookback):
        high = data['high'].iloc[i]
        low = data['low'].iloc[i]

        is_swing_high = all(high > data['high'].iloc[i - j] for j in range(1, lookback + 1)) and \
                        all(high > data['high'].iloc[i + j] for j in range(1, lookback + 1))

        is_swing_low = all(low < data['low'].iloc[i - j] for j in range(1, lookback + 1)) and \
                       all(low < data['low'].iloc[i + j] for j in range(1, lookback + 1))

        if is_swing_high:
            swings.append((data['time'].iloc[i], high, "high"))

        if is_swing_low:
            swings.append((data['time'].iloc[i], low, "low"))

    return swings


swings = find_swings(df)


# -----------------------------
# 3. Plot
# -----------------------------
plt.figure(figsize=(12, 6))
plt.plot(df['time'], df['close'])

for swing in swings:
    if swing[2] == "high":
        plt.scatter(swing[0], swing[1])
    else:
        plt.scatter(swing[0], swing[1])

plt.title("Live EURUSD M15 Structure")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

mt5.shutdown()
