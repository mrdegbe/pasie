import MetaTrader5 as mt5

if not mt5.initialize():
    print("Initialization failed:", mt5.last_error())
    quit()

print("Connected to terminal")

info = mt5.terminal_info()
print("Terminal info:", info)

account_info = mt5.account_info()
print("Account info:", account_info)

mt5.shutdown()
