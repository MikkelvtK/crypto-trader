SHORT_TERM_RATIO = 0.34
LONG_TERM_RATIO = 0.66


class Portfolio:

    def __init__(self, balance):
        self.assets = ["VETUSDT"]
        self.balance = balance
        self.short_term_balance = SHORT_TERM_RATIO * self.balance
        self.long_term_balance = LONG_TERM_RATIO * self.balance
        self.coins = {}
