class CrossingSMA:

    def __init__(self, ma1, ma2):
        self.buy = False
        self.ma1 = ma1
        self.ma2 = ma2
        self.interval = "4h"
        self.type = "LONG"

    def check_for_signal(self, df):
        if df[f"SMA_{self.ma1}"].iloc[-1] > df[f"SMA_{self.ma2}"].iloc[-1] and self.buy is False:
            return "BUY"
        elif df[f"SMA_{self.ma1}"].iloc[-1] < df[f"SMA_{self.ma2}"].iloc[-1] and self.buy is True:
            return "SELL"


class BottomRSI:

    def __init__(self, ma1, ma2):
        self.buy = False
        self.ma1 = ma1
        self.ma2 = ma2
        self.counter = 0
        self.interval = "30m"
        self.type = "SHORT"

    def check_for_signal(self, df):
        if self.buy is True:
            self.counter += 1

        if df["RSI"].iloc[-1] < 30 and self.buy is False:
            return "BUY"
        elif ((df["RSI"].iloc[-1] > 40 or self.counter == 5) and
              self.buy is True):
            return "SELL"
