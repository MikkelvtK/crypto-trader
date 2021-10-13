def get_balance(currency, data):
    for balance in data["balances"]:
        if balance["asset"].lower() == currency:
            return float(balance["free"])


def format_border(message):
    left_border = "<---------------------"
    right_border = ""

    while len(left_border + message + right_border) < 80:
        right_border += "-"

    print(left_border + message + right_border + ">")


