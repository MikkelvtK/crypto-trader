from bot.class_blueprints.data import Data


class Strategy:

    def __init__(self, symbol, interval, name, strategy_type, stop_loss):
        self.symbol = symbol
        self.name = name
        self.interval = interval
        self.type = strategy_type
        self.trailing_stop_loss = stop_loss


class CrossingSMA(Strategy):

    def __init__(self, symbol, interval, name):
        super().__init__(symbol=symbol, interval=interval, name=name, strategy_type="long", stop_loss=False)
        self.__ma1 = 50
        self.__ma2 = 200
        self._current_data = None
        self._is_active = False

    @property
    def current_data(self):
        if self._current_data is None:
            raise Exception("No data has been retrieved yet.")
        return self._current_data

    @current_data.setter
    def current_data(self, data):
        new_data = Data(data=data)
        new_data.set_sma(self.__ma1)
        new_data.set_sma(self.__ma2)
        self._current_data = new_data.df

    @property
    def is_active(self):
        return self._is_active

    def check_for_signal(self):
        """Check if current data gives off a buy or sell signal"""
        ma1_value = self._current_data[f"SMA_{self.__ma1}"].iloc[-1]
        ma2_value = self._current_data[f"SMA_{self.__ma2}"].iloc[-1]

        # If short SMA > long SMA give off buy signal
        if ma1_value > ma2_value and not self._is_active:
            return "buy"

        # If long SMA > short SMA give off sell signal
        elif ma1_value < ma2_value and self._is_active:
            return "sell"
