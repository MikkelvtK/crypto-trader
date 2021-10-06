import sqlalchemy
import psutil
import math
from decorators import *
from database import *
from class_blueprints.trader import TraderAPI
from class_blueprints.order import Order
from class_blueprints.portfolio import Portfolio


class TraderBot:

    def __init__(self, name, strategies, cryptos):

        self._name = name
        self._api = TraderAPI()
        self._strategies = strategies
        self._portfolio = Portfolio(owner=config.USER,
                                    fiat=config.FIAT_MARKET,
                                    cryptos=cryptos)

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

    def balance_request(self):
        """Get float value of total balance (available and currently invested)"""
        for balance in self._api.get_balance()["balances"]:
            if balance["asset"].lower() == self._portfolio.fiat:
                return float(balance["free"])

    # ----- SETUP FOR ORDERS ----- #

    def get_investment_amount(self, symbol):
        """Checks if there is any available currency in current balance to invest"""

        if self._portfolio.fiat_balance < 10:
            return

        if self._portfolio.query_crypto_balance(symbol).balance > 0:
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
            fiat_amount = self.get_investment_amount(strategy.symbol)

            if fiat_amount:
                crypto_coins = fiat_amount / rounded_price
                rounded_coins = self.get_correct_fractional_part(symbol=strategy.symbol,
                                                                 number=crypto_coins, price=False)
                if (rounded_coins * rounded_price) <= fiat_amount:
                    return rounded_price, rounded_coins
                raise Exception("The limit order places an order higher than the given fiat amount.")

        elif action == "sell":
            crypto = self._portfolio.query_crypto_balance(crypto=strategy.symbol)
            crypto_coins = crypto.balance
            rounded_coins = self.get_correct_fractional_part(symbol=strategy.symbol, number=crypto_coins, price=False)
            if crypto_coins == 0:
                return
            return rounded_price, rounded_coins

    # ----- PLACE ORDERS ----- #

    def place_limit_order(self, price, symbol, action, crypto_coins):
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

        return self._api.cancel_orders(symbol=symbol)

    def process_order(self, receipt, strategy):
        crypto = self._portfolio.query_crypto_balance(receipt["symbol"].lower())
        self._portfolio.fiat_balance = self.balance_request()
        investment = float(receipt["price"]) * float(receipt["executedQty"])

        order = Order(
            order_id=receipt["orderId"],
            symbol=receipt["symbol"].lower(),
            price=float(receipt["price"]),
            investment=investment,
            coins=float(receipt["executedQty"]),
            side=receipt["side"].lower(),
            type=receipt["type"].lower(),
            time=receipt["transactTime"],
            status=receipt["status"].lower()
        )

        if receipt["side"].lower() == "buy":
            if strategy.stop_loss:
                stop_loss = strategy.stop_loss.query()
                order.to_sql(engine=self.__engine, stop_loss=stop_loss)
            else:
                order.to_sql(engine=self.__engine)

            # 0.999 is for setting aside the commission few of Binance
            coins = float(receipt["executedQty"]) * 0.999
            value = float(receipt["price"]) * coins
            crypto.update(investment=investment, balance=coins, value=value)
        else:
            order.to_sql(engine=self.__engine, buy_order_id=order.get_last_buy_order(engine=self.__engine).order_id)
            crypto.update()

    # ----- VISUAL FEEDBACK ----- #

    @add_border
    def print_new_data(self, df, strategy):
        """Print new data result"""
        message = f"RETRIEVING DATA FOR {strategy.symbol.upper()}"
        data = df.iloc[-1, :]
        return message, data

    @add_border
    def print_new_order(self, action, asset_symbol):
        """Print when order is placed"""
        new_balance = self._portfolio.fiat_balance
        first_line = f"{action.upper()} ORDER PLACED FOR {asset_symbol.upper()}"
        second_line = f"NEW BALANCE: {round(new_balance, 2)}"
        return first_line, second_line

    # ----- ON/OFF BUTTON ----- #

    def activate(self):
        """Activate the bot"""
        just_posted = False
        self._portfolio.fiat_balance = self.balance_request()

        while True:
            current_time = time.time()

            for strategy in self._strategies:

                if -1 <= (current_time % self.__timer) <= 1:
                    if not just_posted:
                        time.sleep(10)
                        just_posted = True

                    new_data = self._api.get_history(symbol=strategy.symbol,
                                                     interval=strategy.interval_4h,
                                                     limit=200)
                    strategy.current_data_4h = new_data
                    self.print_new_data(df=strategy.current_data_4h, strategy=strategy)
                    action = strategy.check_for_bull_market()

                    if action == "check for opportunity":
                        new_data = self._api.get_history(symbol=strategy.symbol,
                                                         interval=strategy.interval_1h,
                                                         limit=50)
                        strategy.current_data_1h = new_data
                        self.print_new_data(df=strategy.current_data_1h, strategy=strategy)
                        action = strategy.check_for_opportunity()

                    if action is None:
                        continue

                    price, crypto_coins = self.get_coins_to_trade(strategy=strategy, action=action)

                    if crypto_coins is None:
                        continue

                    order_receipt = self.place_limit_order(symbol=strategy.symbol,
                                                           price=price, action=action, crypto_coins=crypto_coins)

                    if order_receipt["status"].lower() == "filled":
                        self.process_order(receipt=order_receipt, strategy=strategy)
                        self.print_new_order(action, strategy.symbol)

            if just_posted:
                print(f"Current CPU usage: {psutil.cpu_percent(4)}.")
                time.sleep(self.__timer - 60)
                just_posted = False
