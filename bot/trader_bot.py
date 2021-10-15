import sqlalchemy
import math
from decorators import *
from database import *
from class_blueprints.order import Order
from functions import format_border
from class_blueprints.stop_loss import TrailingStopLoss
from class_blueprints.trader import get_exchange_info, get_latest_price, post_order, query_order, cancel_order


class TraderBot:

    def __init__(self, name, strategies, portfolio):

        self._name = name
        self._strategies = strategies
        self._portfolio = portfolio
        self.__timer = 900
        self.__engine = sqlalchemy.create_engine(f"sqlite:///{config.db_path}")

    # ----- HANDLING DATA ----- #

    @staticmethod
    def get_correct_fractional_part(symbol, number, price=True):
        """Get the step size for crypto currencies used by the _api"""
        symbol_info = get_exchange_info(symbol)["symbols"][0]

        if price:
            lot_size_filter = symbol_info["filters"][0]
            step_type = "tickSize"
        else:
            lot_size_filter = symbol_info["filters"][2]
            step_type = "stepSize"

        step_size = lot_size_filter[step_type].find("1") - 1

        if step_size < 0:
            return math.floor(number)
        return math.floor(number * 10 ** step_size) / 10 ** step_size

    # ----- SETUP FOR ORDERS ----- #

    def get_investment_amount(self, price):
        """Checks if there is any available currency in current balance to invest"""

        if self._portfolio.fiat_balance < 10:
            return

        active_balances = self._portfolio.get_active_balances_count(price=price)
        available_balances = len(self._portfolio.crypto_balances) - active_balances
        investment = self._portfolio.fiat_balance / available_balances
        if investment > 10:
            return investment

    def get_coins_to_trade(self, strategy, action):
        price = float(get_latest_price(strategy.symbol)["price"])
        rounded_price = self.get_correct_fractional_part(symbol=strategy.symbol, number=price)

        if action == "buy":
            fiat_amount = self.get_investment_amount(price=price)

            if fiat_amount:
                crypto_coins = fiat_amount / rounded_price
                rounded_coins = self.get_correct_fractional_part(symbol=strategy.symbol,
                                                                 number=crypto_coins, price=False)
                if (rounded_coins * rounded_price) <= fiat_amount:
                    return rounded_price, rounded_coins
                print("The limit order places an order higher than the given fiat amount.")

        elif action == "sell":
            crypto = self._portfolio.query_crypto_balance(crypto=strategy.symbol)
            crypto_coins = crypto.balance
            rounded_coins = self.get_correct_fractional_part(symbol=strategy.symbol, number=crypto_coins, price=False)
            if rounded_coins * rounded_price >= 10:
                return rounded_price, rounded_coins
            print("The limit order places an order higher than the given fiat amount.")

    # ----- PLACE ORDERS ----- #

    def place_limit_order(self, symbol, action, strategy):
        """Place limit order"""

        try:
            price, crypto_coins = self.get_coins_to_trade(strategy=strategy, action=action)

        except TypeError:
            print("There is no fiat in your account. No order will be place.")

        else:
            receipt = post_order(asset=symbol, action=action, order_type="limit", price=price,
                                 quantity_type="quantity", amount=crypto_coins)
            confirmation = query_order(asset_symbol=symbol, order_id=receipt["orderId"])

            for _ in range(2):
                if confirmation["status"].lower() == "filled":
                    return confirmation
                else:
                    time.sleep(5)
                    confirmation = query_order(asset_symbol=symbol, order_id=receipt["orderId"])

            order = cancel_order(symbol=symbol, order_id=receipt["orderId"])

            if order["status"] == "canceled":
                print("Limit order was not filled, order is cancelled. Will try again.")
                return self.place_limit_order(symbol=symbol, action=action, strategy=strategy)

    def process_order(self, receipt, strategy):
        self._portfolio.update_portfolio()
        investment = float(receipt["price"]) * float(receipt["executedQty"])

        if receipt["side"].lower() == "buy":
            strategy.stop_loss = TrailingStopLoss()
            strategy.stop_loss.initialise(strategy_name=strategy.name,
                                          symbol=strategy.symbol,
                                          price=float(receipt["price"]))
        else:
            strategy.stop_loss.close_stop_loss()
            strategy.stop_loss = None

        order = Order(
            order_id=receipt["orderId"],
            symbol=receipt["symbol"].lower(),
            price=float(receipt["price"]),
            investment=investment,
            coins=float(receipt["executedQty"]),
            side=receipt["side"].lower(),
            type=receipt["type"].lower(),
            time=receipt["updateTime"],
            status=receipt["status"].lower()
        )

        if receipt["side"].lower() == "buy":
            if strategy.stop_loss:
                stop_loss = strategy.stop_loss.query()
                order.to_sql(engine=self.__engine, stop_loss=stop_loss)
            else:
                order.to_sql(engine=self.__engine)

        else:
            buy_order = order.get_last_buy_order(engine=self.__engine)

            if buy_order:
                order.to_sql(engine=self.__engine, buy_order_id=buy_order.order_id)

    # ----- VISUAL FEEDBACK ----- #

    @staticmethod
    def print_new_data(df, strategy):
        """Print new data result"""
        format_border(f"CURRENT MARKET STATE FOR {strategy.symbol.upper()}: {strategy.market_state.upper()}")
        print(f"\n{df.iloc[-1, :]}\n")

    def print_new_order(self, action, symbol):
        """Print when order is placed"""
        new_balance = self._portfolio.fiat_balance
        crypto = self._portfolio.query_crypto_balance(crypto=symbol)
        format_border(f"{action.upper()} ORDER PLACED FOR {symbol.upper()}")
        format_border(f"NEW FIAT BALANCE: {round(new_balance, 2)}")
        format_border(f"NEW {crypto.crypto.upper()} BALANCE: {round(crypto.balance, 2)}")

    # ----- ON/OFF BUTTON ----- #

    def activate(self):
        """Activate the bot"""
        just_posted = False

        while True:
            current_time = time.time()

            if -1 <= (current_time % self.__timer) <= 1:
                if not just_posted:
                    just_posted = True

                for strategy in self._strategies:
                    try:
                        data, action = strategy.check_for_signal()

                    except TypeError:
                        print("Something went wrong. Continuing")
                        continue

                    self.print_new_data(df=data.df, strategy=strategy)

                    if action == "continue":
                        continue

                    order_receipt = self.place_limit_order(symbol=strategy.symbol, action=action, strategy=strategy)

                    if order_receipt:
                        if order_receipt["status"].lower() == "filled":
                            self.process_order(receipt=order_receipt, strategy=strategy)
                            self.print_new_order(action, strategy.symbol)

                self._portfolio.print_portfolio()

            elif -0.5 <= (current_time % 60) <= 0.5:
                if not just_posted:
                    just_posted = True

                for strategy in self._strategies:
                    action = strategy.check_stop_loss()

                    if action == "sell":
                        order_receipt = self.place_limit_order(symbol=strategy.symbol, action=action, strategy=strategy)

                        if order_receipt:
                            if order_receipt["status"].lower() == "filled":
                                self.process_order(receipt=order_receipt, strategy=strategy)
                                self.print_new_order(action, strategy.symbol)

            if just_posted:
                time.sleep(55)
                just_posted = False
