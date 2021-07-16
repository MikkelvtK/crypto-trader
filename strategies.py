LOG_COLUMNS = ["Timestamp", "Asset", "Action", "Price", "Volume", "Value", "Strategy"]


class CrossingSMA:

    def __init__(self, ma1, ma2):
        self.__name__ = "Crossing SMA"
        self.buy = False
        self.ma1 = ma1
        self.ma2 = ma2
        self.strategy = "long term strategy"

    def check_for_signal(self, df):
        # current_price = df["Close"].iloc[-1]

        if df[f"SMA_{self.ma1}"].iloc[-1] > df[f"SMA_{self.ma2}"].iloc[-1] and self.buy is False:
            print("BUY SIGNAL")
            self.buy = True
        elif df[f"SMA_{self.ma1}"].iloc[-1] < df[f"SMA_{self.ma2}"].iloc[-1] and self.buy is True:
            print("SELL SIGNAL")
            self.buy = False


class BottomRSI:

    def __init__(self, ma1, ma2):
        self.__name__ = "Buy the RSI dip"
        self.buy = False
        self.ma1 = ma1
        self.ma2 = ma2
        self.counter = 0
        self.strategy = "short term strategy"

    def check_for_signal(self, df):

        if self.buy is True:
            self.counter += 1

        if df["RSI"].iloc[-1] < 30 and self.buy is False:
            print("BUY SIGNAL")
            self.buy = True
        elif (df["RSI"].iloc[-1] > 40 or self.counter == 5) and self.buy is True:
            print("SELL SIGNAL")
            self.buy = False
