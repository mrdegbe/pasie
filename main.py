import MetaTrader5 as mt5
import pandas as pd
import mplfinance as mpf
import numpy as np

from utils.dataframe import format_dataframe
from utils.mt5_connector import connect, get_data, shutdown
from utils.structure import determine_structure, find_swings
from utils.liquidity import detect_liquidity_sweep
from utils.choch_bos import detect_choch


symbol = "EURUSDm"

if not connect():
    quit()

# --- Get Data ---
df_h4 = get_data(symbol, mt5.TIMEFRAME_H4)
df_m15 = get_data(symbol, mt5.TIMEFRAME_M15)

# --- Structure ---
swings_h4 = find_swings(df_h4)
structure_h4 = determine_structure(swings_h4)

swings_m15 = find_swings(df_m15)
structure_m15 = determine_structure(swings_m15)

# --- Liquidity ---
liquidity_signal, sweep_index = detect_liquidity_sweep(df_m15, swings_m15)

# --- CHoCH ---
choch_signal, reasons, choch_index = detect_choch(
    df_m15,
    swings_m15,
    structure_m15,
    sweep_index
)

print("4H Bias:", structure_h4)
print("15M Structure:", structure_m15)
print("Liquidity:", liquidity_signal)
print("CHoCH:", choch_signal)

shutdown()



df_m15 = format_dataframe(df_m15)
df_h4 = format_dataframe(df_h4)

# -----------------------------
# 3. Plot Candlestick Chart
# -----------------------------
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
