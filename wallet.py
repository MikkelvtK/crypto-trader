class Portfolio:

    def __init__(self, balance, strategies, df):
        self.assets = ["VETEUR", "LINKEUR"]
        self.total_balance = balance
        self.available_balances = {}
        for strategy in strategies:
            available_balance = float(strategy.ratio * self.total_balance -
                                      df["strategy"].loc[df["strategy"] == strategy.name].sum())
            self.available_balances[strategy.name] = available_balance
        self.active_trades = 0

    def calc_available_balance(self, ratio):
        """Calculate the amount of balance to use for buy order"""
        return ratio / (1 - self.active_trades) * self.total_balance
