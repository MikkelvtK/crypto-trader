class Strategy:

    def __init__(self, interval, strategy_type, ratio):
        self.buy = False
        self.interval = interval
        self.strategy_type = strategy_type
        self.ratio = ratio


class CrossingSMA(Strategy):

    def __init__(self, ma1, ma2, interval, strategy_type, balance):
        super().__init__(interval, strategy_type, balance)
        self.ma1 = ma1
        self.ma2 = ma2

    def check_for_signal(self, df):
        if df[f"SMA_{self.ma1}"].iloc[-1] > df[f"SMA_{self.ma2}"].iloc[-1] and self.buy is False:
            return "BUY"
        elif df[f"SMA_{self.ma1}"].iloc[-1] < df[f"SMA_{self.ma2}"].iloc[-1] and self.buy is True:
            return "SELL"


class BottomRSI(Strategy):

    def __init__(self, interval, strategy_type, balance):
        super().__init__(interval, strategy_type, balance)
        self.counter = 0

    def check_for_signal(self, df):
        if self.buy is True:
            self.counter += 1

        if df["RSI"].iloc[-1] < 30 and self.buy is False:
            return "BUY"
        elif ((df["RSI"].iloc[-1] > 40 or self.counter == 5) and
              self.buy is True):
            return "SELL"
