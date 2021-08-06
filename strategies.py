class Strategy:

    def __init__(self, interval, assets, name, strategy_type, stop_loss):
        self.name = name
        self.assets = assets
        self.interval = interval
        self.type = strategy_type
        self.trailing_stop_loss = stop_loss


class CrossingSMA(Strategy):

    def __init__(self, ma1, ma2, interval, assets, name):
        super().__init__(interval, assets, name, "long", False)
        self.ma1 = ma1
        self.ma2 = ma2

    def check_for_signal(self, df, active, symbol):
        """Check if current data gives off a buy or sell signal"""

        # If short SMA > long SMA give off buy signal
        if df[f"SMA_{self.ma1}"].iloc[-1] > df[f"SMA_{self.ma2}"].iloc[-1] and not active:
            return "buy"

        # If long SMA > short SMA give off sell signal
        elif df[f"SMA_{self.ma1}"].iloc[-1] < df[f"SMA_{self.ma2}"].iloc[-1] and active:
            return "sell"


class BottomRSI(Strategy):

    def __init__(self, interval, assets, name):
        super().__init__(interval, assets, name, "short", True)
        self.current_price = 0
        self.active_stop_losses = []

    def check_for_signal(self, df, active, symbol):
        """Check if current data gives off a buy or sell signal"""
        self.current_price = df["Price"].iloc[-1]

        # When RSI < 30 give off buy signal
        if df["RSI"].iloc[-1] < 30 and not active:
            return "buy"

        # Calculate the trailing stop loss
        for stop_loss in self.active_stop_losses:
            if stop_loss.asset == symbol:
                if self.current_price > stop_loss.highest:
                    stop_loss.highest = self.current_price
                    stop_loss.trail = stop_loss.highest * 0.95

                # When RSI >= 40 give off sell signal
                if df["RSI"].iloc[-1] >= 40 or self.current_price < stop_loss.trail and active:
                    return "sell"


class BollingerBands(Strategy):

    def __init__(self, interval, assets, name):
        super().__init__(interval, assets, name, "short", True)
        self.current_price = 0
        self.active_stop_losses = []

    def check_for_signal(self, df, active, symbol):
        """Check if current data gives off a buy or sell signal"""
        self.current_price = df["Price"].iloc[-1]

        # Determine if price dips below lower Bollinger band and RSI < 30
        if self.current_price < df["Lower"].iloc[-1] and df["RSI"].iloc[-1] < 30 and not active:
            return "buy"

        # Calculate the trailing stop loss
        for stop_loss in self.active_stop_losses:
            if stop_loss.asset == symbol:
                if self.current_price > stop_loss.highest:
                    stop_loss.highest = self.current_price
                    stop_loss.trail = stop_loss.highest * 0.95

                # Determine if price is above upper Bollinger band
                if self.current_price > df["Upper"].iloc[-1] or self.current_price < stop_loss.trail and active:
                    return "sell"


class TrailingStopLoss:

    def __init__(self, symbol, current_price):
        self.asset = symbol
        self.highest = current_price
        self.trail = self.highest * 0.95
