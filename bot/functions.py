def get_balance(currency, data):
    for balance in data["balances"]:
        if balance["asset"].lower() == currency:
            return float(balance["free"])
