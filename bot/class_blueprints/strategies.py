from class_blueprints.data import Data
from class_blueprints.stop_loss import TrailingStopLoss


class Strategy:

    def __init__(self, symbol, name):
        self._name = name
        self._symbol = symbol
        self._interval_4h = ("4h", 14400)
        self._interval_1h = ("1h", 3600)
        self._type = "hodl"
        self.__ma1 = 50
        self.__ma2 = 200
        self.__rsi = 14
        self._current_data_4h = None
        self._current_data_1h = None
        self._bull_market = False
        self._stop_loss = None

    @property
    def name(self):
        return self._name

    @property
    def symbol(self):
        return self._symbol

    @property
    def interval_4h(self):
        return self._interval_4h

    @property
    def interval_1h(self):
        return self._interval_1h

    @property
    def type(self):
        return self._type

    @property
    def current_data_4h(self):
        if self._current_data_4h is None:
            raise Exception("No data has been retrieved yet.")
        return self._current_data_4h

    @current_data_4h.setter
    def current_data_4h(self, data):
        new_data = Data(data=data)
        new_data.set_sma(self.__ma1)
        new_data.set_sma(self.__ma2)
        self._current_data_4h = new_data.df

    @property
    def current_data_1h(self):
        if self._current_data_1h is None:
            raise Exception("No data has been retrieved yet.")
        return self._current_data_1h

    @current_data_1h.setter
    def current_data_1h(self, data):
        new_data = Data(data=data)
        new_data.set_rsi()
        self._current_data_1h = new_data.df

    @property
    def bull_market(self):
        return self._bull_market

    @property
    def stop_loss(self):
        return self._stop_loss

    def check_for_bull_market(self):
        """Check if current data gives off a buy or sell signal"""
        ma1_value = self._current_data_4h[f"SMA_{self.__ma1}"].iloc[-1]
        ma2_value = self._current_data_4h[f"SMA_{self.__ma2}"].iloc[-1]

        # If short SMA > long SMA give off buy signal
        if ma1_value > ma2_value and not self._bull_market:
            return "buy"

        # If long SMA > short SMA give off sell signal
        elif ma1_value < ma2_value and self._bull_market:
            return "sell"

        elif not self._bull_market:
            return "check for opportunity"

    def check_for_opportunity(self):
        rsi = self._current_data_1h["RSI"].iloc[-1]
        price = self._current_data_1h["Price"].iloc[-1]

        if rsi <= 25 and not self._stop_loss:
            self._stop_loss = TrailingStopLoss(strategy_name=self._name, symbol=self._symbol, current_price=price)
            return "buy"

        elif rsi >= 30 and self._stop_loss:
            self._stop_loss = None
            return "sell"

        elif self._stop_loss:
            self._stop_loss.adjust_stop_loss(price=price)
