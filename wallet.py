class Portfolio:

    def __init__(self, balance):
        self.assets = ["VETEUR"]
        self.balance = balance
        self.active_trades = 0

    def calc_available_balance(self, ratio):
        return ratio / (1 - self.active_trades) * self.balance
