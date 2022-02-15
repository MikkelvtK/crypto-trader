import sqlalchemy
import math
from decorators import *
from functions import format_border
from class_blueprints.stop_loss import TrailingStopLoss
from class_blueprints.trader import get_exchange_info, get_latest_price, post_order, query_order, cancel_order
from class_blueprints.trader import cancel_all_orders
import os
import config
import sys


class TraderBot:

    def __init__(self, name, strategies, portfolio):

        self._name = name
        self._strategies = strategies
        self._portfolio = portfolio
        self.__timer = 1800
        self.__engine = sqlalchemy.create_engine(f"sqlite:///{config.db_path}")

    # ----- HANDLING DATA ----- #

    @staticmethod
    def get_correct_fractional_part(symbol, quantity, price=True):
        """
        Determines how many numbers the fractional part of the quantity may have according to Binance API rules.

        :param symbol: (str) The symbol of the asset of which the interval needs to be retrieved.
        :param quantity: (float) The number that needs to be adjusted according to Binance API rules.
        :param price: (float) Tells method if it's dealing with the price of an asset or with an amount of coins.
        Default is True.
        :return: The adjusted quantity.
        """
        symbol_info = get_exchange_info(symbol)["symbols"][0]

        if price:
            lot_size_filter = symbol_info["filters"][0]
            step_type = "tickSize"
        else:
            lot_size_filter = symbol_info["filters"][2]
            step_type = "stepSize"

        step_size = lot_size_filter[step_type].find("1") - 1

        if step_size < 0:
            return math.floor(quantity)
        return math.floor(quantity * 10 ** step_size) / 10 ** step_size

    # ----- SETUP FOR ORDERS ----- #

    def get_investment_amount(self, price):
        """
        Calculates how much can be invested in an asset.

        :param price: (float) The current price of the asset.
        :return: The investment amount if possible. Returns none if nothing can be invested.
        """

        if self._portfolio.fiat_balance < 10:
            return

        active_balances = self._portfolio.get_active_balances_count(price=price)
        available_balances = len(self._portfolio.crypto_balances) - active_balances
        investment = self._portfolio.fiat_balance / available_balances
        if investment > 10:
            return investment

    def get_coins_to_trade(self, strategy, action):
        """
        Determines the rounded amount according to Binance API rules to place for a limit order.

        :param strategy: The strategy object that is currently used.
        :param action: (str) The actions in string format that the limit order will execute. Can be
        either "buy" or "sell".
        :return: (tuple) Returns the price and asset quantity; ready to be used for the order.
        """

        price = float(get_latest_price(strategy.symbol)["price"])
        crypto = self._portfolio.query_crypto_balance(crypto=strategy.symbol)

        if action == "buy":
            fiat_amount = self.get_investment_amount(price=price)

            # Will place the buy price slightly above the current price to make sure the limit order will be executed.
            rounded_price = self.get_correct_fractional_part(symbol=strategy.symbol, quantity=price * 1.001)

            if fiat_amount:
                crypto_coins = fiat_amount / rounded_price
                rounded_coins = self.get_correct_fractional_part(symbol=strategy.symbol, quantity=crypto_coins,
                                                                 price=False)
                if (rounded_coins * rounded_price) <= fiat_amount:
                    return rounded_price, rounded_coins
                print("The limit order places an order higher than the given fiat amount.")

        elif action == "sell":

            # Will place the buy price slightly below the current price to make sure the limit order will be executed.
            rounded_price = self.get_correct_fractional_part(symbol=strategy.symbol, quantity=price * 0.999)
            crypto_coins = crypto.balance
            rounded_coins = self.get_correct_fractional_part(symbol=strategy.symbol, quantity=crypto_coins, price=False)

            if rounded_coins * rounded_price >= 10:
                return rounded_price, rounded_coins
            print("The limit order places an order higher than the given fiat amount.")

    # ----- PLACE ORDERS ----- #

    def place_limit_order(self, symbol, action, strategy):
        """
        Places a limit order with the Binance API.

        :param symbol: (str) The symbol of the asset that is to be traded.
        :param action: (str) The action that the limit order will execute. Can be either "buy" or "sell".
        :param strategy: (object) The strategy that is currently used.
        :return: (dict) Returns the receipt (response from Binance API) in a dictionary.
        """

        try:
            price, crypto_coins = self.get_coins_to_trade(strategy=strategy, action=action)

        except TypeError:
            print("There is no fiat in your account. No order will be place.")

        else:
            try:
                receipt = post_order(asset=symbol, action=action, order_type="limit", price=price,
                                     quantity_type="quantity", amount=crypto_coins)
                confirmation = query_order(asset_symbol=symbol, order_id=receipt["orderId"])

                # Will check if the limit order is filled. After a certain amount of time it will cancel the
                # order and try again.
                for _ in range(2):
                    if confirmation["status"].lower() == "filled":
                        return confirmation
                    else:
                        time.sleep(5)
                        confirmation = query_order(asset_symbol=symbol, order_id=receipt["orderId"])

                order = cancel_order(symbol=symbol, order_id=receipt["orderId"])

            except BinanceAccountIssue:
                os.system(config.command)
                sys.exit("Restarting bot. Please fix issue if it persists.")

            else:
                if order["status"] == "canceled":
                    print("Limit order was not filled, order is cancelled. Will try again.")
                    return self.place_limit_order(symbol=symbol, action=action, strategy=strategy)

    def process_order(self, receipt, strategy):
        """
        Will process the order and adjust all attributes if the order is filled.

        :param receipt: (dict) The receipt response of the limit order from Binance API.
        :param strategy: (object The strategy that is currently used.
        """

        self._portfolio.update_portfolio()

        if receipt["side"].lower() == "buy":
            strategy.stop_loss = TrailingStopLoss()
            if strategy.market_state == "bull":
                strategy.stop_loss.initialise(strategy_name=strategy.name,
                                              symbol=strategy.symbol,
                                              price=float(receipt["price"]),
                                              trail_ratio=0.95)
            elif strategy.market_state == "bear":
                strategy.stop_loss.initialise(strategy_name=strategy.name,
                                              symbol=strategy.symbol,
                                              price=float(receipt["price"]),
                                              trail_ratio=0.95)
        else:
            strategy.stop_loss.close_stop_loss()
            strategy.stop_loss = None

    # ----- VISUAL FEEDBACK ----- #

    @staticmethod
    def print_new_data(df, strategy):
        """
        Prints the new data in the terminal for visual feedback to the user.

        :param df: (DataFrame) A pandas dataframe containing latest price data of an asset.
        :param strategy: (object) Strategy object currently being used.
        """

        format_border(f"CURRENT MARKET STATE FOR {strategy.symbol.upper()}: {strategy.market_state.upper()}")
        print(f"\n{df.iloc[-1, :]}\n")

    def print_new_order(self, action, symbol):
        """
        Prints the new order that was placed with the new balances that changed with it.

        :param action: (str) The action that the limit order will execute. Can be either "buy" or "sell".
        :param symbol: (str) The symbol of the asset that was traded.
        """

        new_balance = self._portfolio.fiat_balance
        crypto = self._portfolio.query_crypto_balance(crypto=symbol)
        format_border(f"{action.upper()} ORDER PLACED FOR {symbol.upper()}")
        format_border(f"NEW FIAT BALANCE: {round(new_balance, 2)}")
        format_border(f"NEW {crypto.crypto.upper()} BALANCE: {round(crypto.balance, 2)}")

    # ----- ON/OFF BUTTON ----- #

    def activate(self):
        """Activate the main loop of the bot"""
        just_posted = False

        for symbol, crypto in self._portfolio.crypto_balances.items():
            try:
                cancel_all_orders(symbol=symbol)
            except BinanceAccountIssue:
                print(f"There are no orders to cancel for {symbol.upper()}.")

        while True:
            current_time = time.time()

            if -1 <= (current_time % 60) <= 1:

                for strategy in self._strategies:
                    action = None

                    if -1 <= (current_time % self.__timer) <= 1:
                        if not just_posted:
                            just_posted = True

                        try:
                            data, action = strategy.check_for_signal()

                        except TypeError:
                            print("Something went wrong. Continuing")
                            continue

                        self.print_new_data(df=data.df, strategy=strategy)
                        self._portfolio.print_portfolio()

                    if action:

                        if action == "continue":
                            continue

                        order_receipt = self.place_limit_order(symbol=strategy.symbol, action=action, strategy=strategy)

                        if order_receipt:
                            if order_receipt["status"].lower() == "filled":
                                self.print_new_order(action, strategy.symbol)

            if just_posted:
                time.sleep(55)
                just_posted = False
