import math


class Portfolio:

    def __init__(self, balance):
        self.assets = ["VETEUR", "LINKEUR"]
        self.balance = balance
        self.coins = {}
        self.active_trades = 0

    def calc_available_balance(self, ratio):
        return ratio / (1 - self.active_trades) * self.balance

    def calc_order_quantity(self, tick, coin):
        return math.floor(self.coins[coin] * 10 ** tick) / float(10 ** tick)
