class Portfolio:

    def __init__(self, balance):
        self.assets = ["VETEUR", "LINKEUR"]
        self.balance = balance
        self.active_trades = 0

    def calc_available_balance(self, ratio):
        """Calculate the amount of balance to use for buy order"""
        return ratio / (1 - self.active_trades) * self.balance
