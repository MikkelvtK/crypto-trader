class Portfolio:

    def __init__(self, trader):
        self.trader = trader
        self.assets = ["VETEUR"]
        self.balance = self.trader.get_balance()
        self.coins = {}

    def get_balance(self):
        self.balance = self.trader.get_balance()
