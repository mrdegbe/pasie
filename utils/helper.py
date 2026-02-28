# utils/helper.py


# Pip size helper function
def get_pip_size(symbol):
    if "JPY" in symbol:
        return 0.01
    return 0.0001


PAIRS = [
    "EURUSDm",
    "GBPUSDm",
    "AUDUSDm",
    "NZDUSDm",
    "USDCHFm",
    "USDCADm",
    "USDJPYm",
    "GBPJPYm",
    "XAUUSDm",
]
