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

    def __init__(self, interval, name, balance):
        super().__init__(interval, name, balance)
        self.trailing_stop_losses = []

    def check_for_signal(self, df, asset):
        """Check if current data gives off a buy or sell signal"""
        current_price = df["Price"].iloc[-1]

        # Determine if price dips below lower Bollinger band and RSI < 30
        if df["Price"].iloc[-1] < df["Lower"].iloc[-1] and df["RSI"].iloc[-1] < 30:
            trailing_stop_loss = TrailingStopLoss(asset, current_price) # Dit moet ik nog even nakijken. Werkt zo niet goed
            self.trailing_stop_losses.append(trailing_stop_loss)
            return "buy"

        # Calculate the trailing stop loss
        for stop_loss in self.trailing_stop_losses:
            if stop_loss.asset == asset:
                if current_price > stop_loss.highest:
                    stop_loss.highest = current_price
                    stop_loss.trail = stop_loss.highest * 0.95

                # Determine if price is above upper Bollinger band
                if current_price > df["Upper"].iloc[-1] or df["Price"].iloc[-1] < stop_loss.trail:
                    self.trailing_stop_losses.remove(stop_loss)
                    return "sell"


class TrailingStopLoss:

    def __init__(self, symbol, current_price):
        self.asset = symbol
        self.highest = current_price
        self.trail = self.highest * 0.95
