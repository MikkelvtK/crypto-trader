from class_blueprints.data import Data
from class_blueprints.stop_loss import TrailingStopLoss


class Strategy:

    def __init__(self, symbol, name, api):
        self._name = name
        self._symbol = symbol
        self._api = api
        self._type = "hodl"
        self._market_state = None

        try:
            self._stop_loss = TrailingStopLoss()
            self._stop_loss.load(symbol=self._symbol)
        except AttributeError:
            print("No Active stop loss found.")
            self._stop_loss = None

    # ----- GETTERS / SETTERS ----- #

    @property
    def name(self):
        return self._name

    @property
    def symbol(self):
        return self._symbol

    @property
    def type(self):
        return self._type

    @property
    def stop_loss(self):
        return self._stop_loss

    @property
    def market_state(self):
        return self._market_state

    # ----- CLASS METHODS ----- #
    def _get_market_state_data(self):
        new_data = Data(data=self._api.get_history(symbol=self._symbol, interval="4h", limit=1000))
        new_data.set_ema(window=50)
        new_data.set_ema(window=200)
        return new_data

    def _get_bull_scenario_data(self):
        new_data = Data(data=self._api.get_history(symbol=self._symbol, interval="15m", limit=1000))
        new_data.set_ema(window=9)
        new_data.set_ema(window=20)
        return new_data

    def _get_bear_scenario_data(self):
        new_data = Data(data=self._api.get_history(symbol=self._symbol, interval="1h", limit=50))
        new_data.set_rsi()
        return new_data

    def check_for_signal(self):
        """Check if current data gives off a buy or sell signal"""
        data = self._get_market_state_data()

        if data.df["EMA_50"].iloc[-1] > data.df["EMA_200"].iloc[-1]:
            self._market_state = "bull"

            bull_data = self._get_bull_scenario_data()
            price = bull_data.df["Price"].iloc[-1]

            if bull_data.df["EMA_9"].iloc[-1] > bull_data.df["EMA_20"].iloc[-1] and not self._stop_loss:
                self._stop_loss = TrailingStopLoss()
                self._stop_loss.initialise(strategy_name=self._name, symbol=self._symbol, price=price)
                return bull_data, "buy"

            elif bull_data.df["EMA_9"].iloc[-1] < bull_data.df["EMA_20"].iloc[-1] and self._stop_loss:
                if price > self._stop_loss.buy_price:
                    self._stop_loss.close_stop_loss()
                    self._stop_loss = None
                    return bull_data, "sell"

                elif price < self._stop_loss.trail:
                    self._stop_loss.close_stop_loss()
                    self._stop_loss = None
                    return bull_data, "sell"

            if self._stop_loss:
                self._stop_loss.adjust_stop_loss(price=price)

            return bull_data, "continue"

        elif data.df["EMA_50"].iloc[-1] < data.df["EMA_200"].iloc[-1]:
            self._market_state = "bear"

            bear_data = self._get_bear_scenario_data()
            price = bear_data.df["Price"].iloc[-1]

            if bear_data.df["RSI"].iloc[-1] <= 30 and not self._stop_loss:
                self._stop_loss = TrailingStopLoss()
                self._stop_loss.initialise(strategy_name=self._name, symbol=self._symbol, price=price)
                return bear_data, "buy"

            elif bear_data.df["RSI"].iloc[-1] >= 35 and self._stop_loss:
                self._stop_loss.close_stop_loss()
                self._stop_loss = None
                return bear_data, "sell"

            elif self._stop_loss:
                if price < self._stop_loss.trail:
                    self._stop_loss.close_stop_loss()
                    self._stop_loss = None
                    return bear_data, "sell"
                self._stop_loss.adjust_stop_loss(price=price)

            return bear_data, "continue"
