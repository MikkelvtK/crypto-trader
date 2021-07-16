import pandas as pd

LOG_COLUMNS = ["Timestamp", "Asset", "Action", "Price", "Volume", "Value", "Strategy"]


class LongTermStrategy:

    def __init__(self, ma1, ma2):
        # self.wallet = wallet
        # self.asset = asset
        self.buy = False
        self.ma1 = ma1
        self.ma2 = ma2
        # self.engine = db_connection

    def check_for_signal(self, df):
        # current_price = df["Close"].iloc[-1]

        if df[f"SMA_{self.ma1}"].iloc[-1] > df[f"SMA_{self.ma2}"].iloc[-1] and self.buy is False:
            print("BUY SIGNAL")
            self.buy = True
        elif df[f"SMA_{self.ma1}"].iloc[-1] < df[f"SMA_{self.ma2}"].iloc[-1] and self.buy is True:
            print("SELL SIGNAL")
            self.buy = False


class ShortTermStrategy:

    def __init__(self, ma1, ma2):
        self.buy = False
        self.ma1 = ma1
        self.ma2 = ma2
        self.counter = 0

    def check_for_signal(self, df):
        current_price = df["Price"].iloc[-1]

        if self.buy is True:
            self.counter += 1

        if df["RSI"].iloc[-1] < 25 and self.buy is False:
            print("BUY SIGNAL")
            self.buy = True
        elif df["RSI"].iloc[-1] > 40 or (self.counter >= 5 and current_price > df["Price"].iloc[-self.counter]):
            if self.buy is True:
                print("SELL SIGNAL")
                self.buy = False
