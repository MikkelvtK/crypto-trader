from class_blueprints.data import Data
from class_blueprints.stop_loss import TrailingStopLoss
from functions import get_balance
import config


class Strategy:

    def __init__(self, symbol, name, api):
        self._name = name
        self._symbol = symbol
        self._api = api
        self._type = "hodl"
        self._market_state = None
        self._stop_loss = self._set_stop_loss()

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

    @stop_loss.setter
    def stop_loss(self, action):
        self._stop_loss = action

    def _set_stop_loss(self):
        try:
            stop_loss = TrailingStopLoss()
            stop_loss.load(symbol=self._symbol)

        except AttributeError:
            print("No Active stop loss found. Checking balance.")
            price = float(self._api.get_latest_price(asset=self._symbol)["price"])

            for crypto in config.CRYPTOS:
                if crypto in self._symbol:
                    balance = get_balance(currency=crypto, data=self._api.get_balance())
                    if balance * price > 10:
                        print("Substantial balance found. Setting trailing stop loss.")
                        stop_loss = TrailingStopLoss()
                        stop_loss.initialise(strategy_name=self._name, symbol=self._symbol, price=price)
                        return stop_loss
                    else:
                        print("No substantial balance found. Not setting trailing stop loss.")
                        return None

        else:
            price = float(self._api.get_latest_price(asset=self._symbol)["price"])

            for crypto in config.CRYPTOS:
                if crypto in self._symbol:
                    balance = get_balance(currency=crypto, data=self._api.get_balance())
                    if balance * price < 10:
                        print("Something must have gone wrong, no active trade was found. Closing stop loss and\n"
                              "setting it to none.")
                        stop_loss.close_stop_loss()
                        return None

            return stop_loss

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
        new_data.set_ema(window=8)
        new_data.set_ema(window=21)
        return new_data

    def _get_bear_scenario_data(self):
        new_data = Data(data=self._api.get_history(symbol=self._symbol, interval="1h", limit=50))
        new_data.set_rsi()
        return new_data

    def check_stop_loss(self):
        price = float(self._api.get_latest_price(asset=self._symbol)["price"])

        if self._stop_loss:
            if price < self._stop_loss.trail and price < self._stop_loss.buy_price:
                print("Trailing stop loss is triggered. Crypto will be sold.")
                return "sell"
            self._stop_loss.adjust_stop_loss(price=price)

    def check_for_signal(self):
        """Check if current data gives off a buy or sell signal"""
        data = self._get_market_state_data()

        if data.df["EMA_50"].iloc[-1] > data.df["EMA_200"].iloc[-1]:
            self._market_state = "bull"

            bull_data = self._get_bull_scenario_data()
            price = bull_data.df["Price"].iloc[-1]

            if bull_data.df["EMA_8"].iloc[-1] > bull_data.df["EMA_21"].iloc[-1] and not self._stop_loss:
                return bull_data, "buy"

            elif bull_data.df["EMA_8"].iloc[-1] < bull_data.df["EMA_21"].iloc[-1] and self._stop_loss:
                if price > self._stop_loss.buy_price:
                    return bull_data, "sell"

            return bull_data, "continue"

        elif data.df["EMA_50"].iloc[-1] < data.df["EMA_200"].iloc[-1]:
            self._market_state = "bear"

            bear_data = self._get_bear_scenario_data()

            if bear_data.df["RSI"].iloc[-1] <= 30 and not self._stop_loss:
                return bear_data, "buy"

            elif bear_data.df["RSI"].iloc[-1] >= 35 and self._stop_loss:
                return bear_data, "sell"

            return bear_data, "continue"
