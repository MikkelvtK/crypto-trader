class Strategy:

    def __init__(self, interval, strategy_type, ratio):
        self.active_asset = []
        self.interval = interval
        self.strategy_type = strategy_type
        self.ratio = ratio


class CrossingSMA(Strategy):

    def __init__(self, ma1, ma2, interval, strategy_type, balance):
        super().__init__(interval, strategy_type, balance)
        self.ma1 = ma1
        self.ma2 = ma2

    def check_for_signal(self, df, asset):
        if df[f"SMA_{self.ma1}"].iloc[-1] > df[f"SMA_{self.ma2}"].iloc[-1] and asset not in self.active_asset:
            return "BUY"

        elif df[f"SMA_{self.ma1}"].iloc[-1] < df[f"SMA_{self.ma2}"].iloc[-1] and asset in self.active_asset:
            return "SELL"


class BottomRSI(Strategy):

    def __init__(self, interval, strategy_type, balance):
        super().__init__(interval, strategy_type, balance)
        self.counter = 0

    def check_for_signal(self, df, asset):
        if asset in self.active_asset:
            self.counter += 1

        if df["RSI"].iloc[-1] < 30 and asset not in self.active_asset:
            return "BUY"

        elif (df["RSI"].iloc[-1] >= 40 or self.counter == 5) and asset in self.active_asset:
            self.counter = 0
            return "SELL"


class BollingerBands(Strategy):

    def __init__(self, interval, strategy_type, balance):
        super().__init__(interval, strategy_type, balance)
        self.highest = 0
        self.trail = 0

    def check_for_signal(self, df, asset):
        if asset in self.active_asset:
            if df["Price"].iloc[-1] > self.highest:
                self.highest = df["Price"].iloc[-1]
                self.trail = self.highest * 0.95

        if df["Price"].iloc[-1] < df["Lower"].iloc[-1] and df["RSI"].iloc[-1] < 30:
            if asset not in self.active_asset:
                self.highest = df["Price"].iloc[-1]
                self.trail = self.highest * 0.95
                return "BUY"

        elif self.trail != 0 and asset in self.active_asset:
            if df["Price"].iloc[-1] > df["Upper"].iloc[-1] or df["Price"].iloc[-1] < self.trail:
                self.highest = 0
                self.trail = 0
                return "SELL"
