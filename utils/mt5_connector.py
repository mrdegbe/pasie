import MetaTrader5 as mt5
import pandas as pd


def connect():
    if not mt5.initialize():
        print("Initialization failed:", mt5.last_error())
        return False

    print("MT5 connected")
    return True


def get_data(symbol, timeframe, bars=300):
    if not mt5.symbol_select(symbol, True):
        print("Failed to select symbol")
        return None

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)

    if rates is None:
        print("Failed to get rates:", mt5.last_error())
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'tick_volume': 'Volume'
    }, inplace=True)

    df.set_index('time', inplace=True)

    return df


def shutdown():
    mt5.shutdown()
