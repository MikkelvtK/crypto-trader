class Portfolio:

    def __init__(self, balance):
        self.assets = ["VETEUR", "ADAEUR"]
        self.balance = balance
        self.coins = {}
        self.active_trades = 0

    def calc_available_balance(self, ratio):
        return ratio / (1 - self.active_trades) * self.balance
