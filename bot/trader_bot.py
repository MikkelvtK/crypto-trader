import sqlalchemy
import psutil
import math
from decorators import *
from database import *
from class_blueprints.order import Order
from class_blueprints.portfolio import Portfolio
from functions import get_balance


class TraderBot:

    def __init__(self, name, strategies, cryptos, api):

        self._name = name
        self._api = api
        self._strategies = strategies
        self._portfolio = Portfolio(owner=config.USER,
                                    fiat=config.FIAT_MARKET,
                                    cryptos=cryptos,
                                    api=self._api)

        self.__timer = 300
        self.__engine = sqlalchemy.create_engine(f"sqlite:///{config.db_path}")

    # ----- HANDLING DATA ----- #

    def get_correct_fractional_part(self, symbol, number, price=True):
        """Get the step size for crypto currencies used by the _api"""
        symbol_info = self._api.get_exchange_info(symbol)["symbols"][0]

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

    def get_investment_amount(self):
        """Checks if there is any available currency in current balance to invest"""

        if self._portfolio.fiat_balance < 10:
            return

        active_balances = self._portfolio.get_active_balances_count()
        available_balances = len(self._portfolio.crypto_balances) - active_balances
        investment = self._portfolio.fiat_balance / available_balances
        if investment > 10:
            return investment

    def get_coins_to_trade(self, strategy, action):
        price = float(self._api.get_latest_price(strategy.symbol)["price"])
        rounded_price = self.get_correct_fractional_part(symbol=strategy.symbol, number=price)

        if action == "buy":
            fiat_amount = self.get_investment_amount()

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

    def place_limit_order(self, price, symbol, action, crypto_coins, strategy):
        """Place limit order"""

        receipt = self._api.post_order(asset=symbol, action=action, order_type="limit", price=price,
                                       quantity_type="quantity", amount=crypto_coins)

        confirmation = self._api.query_order(asset_symbol=symbol, order_id=receipt["orderId"])

        for _ in range(5):
            if confirmation["status"].lower() == "filled":
                return confirmation
            else:
                time.sleep(5)
                confirmation = self._api.query_order(asset_symbol=symbol, order_id=receipt["orderId"])

        if action == "buy":
            strategy.stop_loss.close_stop_loss()
            strategy.stop_loss = None

        cancel = self._api.cancel_order(symbol=symbol, order_id=receipt["orderId"])

        if cancel["status"].lower() == "cancelled":
            print("Limit order was not filled, order is cancelled.")

    def process_order(self, receipt, strategy):
        crypto = self._portfolio.query_crypto_balance(receipt["symbol"].lower())
        crypto.balance = get_balance(currency=crypto.crypto, data=self._api.get_balance()["balances"])
        self._portfolio.fiat_balance = get_balance(currency=self._portfolio.fiat,
                                                   data=self._api.get_balance()["balances"])
        investment = float(receipt["price"]) * float(receipt["executedQty"])

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
            order.to_sql(engine=self.__engine, buy_order_id=order.get_last_buy_order(engine=self.__engine).order_id)

    # ----- VISUAL FEEDBACK ----- #

    @add_border
    def print_new_data(self, df, strategy):
        """Print new data result"""
        message = f"CURRENT MARKET STATE FOR {strategy.symbol.upper()}: {strategy.market_state.upper()}"
        data = df.iloc[-1, :]
        return message, data

    @add_border
    def print_new_order(self, action, symbol):
        """Print when order is placed"""
        new_balance = self._portfolio.fiat_balance
        crypto = self._portfolio.query_crypto_balance(crypto=symbol)
        first_line = f"{action.upper()} ORDER PLACED FOR {symbol.upper()}"
        second_line = f"NEW FIAT BALANCE: {round(new_balance, 2)}"
        third_line = f"NEW CRYPTO BALANCE: {round(crypto.balance, 2)}"
        return first_line, second_line, third_line

    # ----- ON/OFF BUTTON ----- #

    def activate(self):
        """Activate the bot"""
        just_posted = False

        self._portfolio.fiat_balance = get_balance(currency=self._portfolio.fiat,
                                                   data=self._api.get_balance()["balances"])
        print(f"Current balance: {round(self._portfolio.fiat_balance, 2)}.")

        for key, crypto in self._portfolio.crypto_balances.items():
            print(f"Current balance for {crypto.get_symbol()}: {crypto.balance}.")

        while True:
            current_time = time.time()

            for strategy in self._strategies:

                if -1 <= (current_time % self.__timer) <= 1:
                    if not just_posted:
                        time.sleep(10)
                        just_posted = True

                    try:
                        data, action = strategy.check_for_signal()
                    except TypeError:
                        print("Something went wrong. Continuing")
                        continue

                    self.print_new_data(df=data.df, strategy=strategy)

                    if action == "continue":
                        continue

                    try:
                        price, crypto_coins = self.get_coins_to_trade(strategy=strategy, action=action)
                    except TypeError:
                        print("There is no fiat in your account. No order will be place.")
                        continue

                    order_receipt = self.place_limit_order(symbol=strategy.symbol, price=price, action=action,
                                                           crypto_coins=crypto_coins, strategy=strategy)

                    if order_receipt["status"].lower() == "filled":
                        self.process_order(receipt=order_receipt, strategy=strategy)
                        self.print_new_order(action, strategy.symbol)

            if just_posted:
                print(f"Current CPU usage: {psutil.cpu_percent(4)}.")
                time.sleep(self.__timer - 60)
                just_posted = False
