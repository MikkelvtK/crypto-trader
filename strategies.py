import pandas as pd


class Strategy:

    def __init__(self, interval, name, type):
        self.name = name
        self.interval = interval
        self.ratio = ratio
        self.type = type

    def set_active_assets(self, db_engine):
        """Sets which assets are currently active for the strategy"""
        df = pd.read_sql("active_trades", db_engine)
        df = df.set_index("asset")
        return df.loc[df["strategy"] == self.name]


class CrossingSMA(Strategy):

    def __init__(self, ma1, ma2, interval, name, balance, db_engine):
        super().__init__(interval, name, balance, db_engine)
        self.ma1 = ma1
        self.ma2 = ma2

    def check_for_signal(self, df, asset):
        """Check if current data gives off a buy or sell signal"""

        # If short SMA > long SMA give off buy signal
        if df[f"SMA_{self.ma1}"].iloc[-1] > df[f"SMA_{self.ma2}"].iloc[-1] and \
                asset not in self.active_assets.index.values:
            return "BUY"

        # If long SMA > short SMA give off sell signal
        elif df[f"SMA_{self.ma1}"].iloc[-1] < df[f"SMA_{self.ma2}"].iloc[-1] and \
                asset in self.active_assets.index.values:
            return "SELL"


class BottomRSI(Strategy):

    def __init__(self, interval, name, balance, db_engine):
        super().__init__(interval, name, balance, db_engine)
        self.counter = 0

    def check_for_signal(self, df, asset):
        """Check if current data gives off a buy or sell signal"""

        # Count intervals since asset was bought
        if asset in self.active_assets:
            self.counter += 1

        # When RSI < 30 give off buy signal
        if df["RSI"].iloc[-1] < 30 and asset not in self.active_assets.index.values:
            return "BUY"

        # When RSI >= 40 give off sell signal
        elif (df["RSI"].iloc[-1] >= 40 or self.counter == 5) and asset in self.active_assets.index.values:
            self.counter = 0
            return "SELL"


class BollingerBands(Strategy):

    def __init__(self, interval, name, balance, db_engine):
        super().__init__(interval, name, balance, db_engine)
        self.highest = 0
        self.trail = 0

    def check_for_signal(self, df, asset):
        """Check if current data gives off a buy or sell signal"""

        # Calculate the trailing stop loss
        if asset in self.active_assets.index.values:
            if df["Price"].iloc[-1] > self.highest:
                self.highest = df["Price"].iloc[-1]
                self.trail = self.highest * 0.95

        # Determine if price dips below lower Bollinger band and RSI < 30
        if df["Price"].iloc[-1] < df["Lower"].iloc[-1] and df["RSI"].iloc[-1] < 30:
            if asset not in self.active_assets.index.values:
                self.highest = df["Price"].iloc[-1]
                self.trail = self.highest * 0.95
                return "BUY"

        # Determine if price is above upper Bollinger band
        elif self.trail != 0 and asset in self.active_assets.index.values:
            if df["Price"].iloc[-1] > df["Upper"].iloc[-1] or df["Price"].iloc[-1] < self.trail:
                self.highest = 0
                self.trail = 0
                return "SELL"
