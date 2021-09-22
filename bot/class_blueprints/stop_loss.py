class TrailingStopLoss:

    def __init__(self, strategy_name, asset_symbol, current_price):
        self.strategy_name = strategy_name
        self.asset = asset_symbol
        self.highest = current_price
        self.trail = self.calculate_stop_loss()

    def adjust_stop_loss(self, price):
        """Adjust current highest point of the trailing stop loss if needed."""
        if price > self.highest:
            self.highest = price
            self.trail = self.calculate_stop_loss()

    def calculate_stop_loss(self):
        return self.highest * 0.95
