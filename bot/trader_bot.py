import sqlalchemy
import math
from decorators import *
from database import *
from class_blueprints.trader import TraderAPI
from class_blueprints.order import Order
from class_blueprints.portfolio import Portfolio


class TraderBot:

    def __init__(self, name, strategies, cryptos):

        # Setup up all parameters given
        self.name = name
        self.api = TraderAPI()
        self.strategies = strategies
        self.portfolio = Portfolio(owner=config.USER,
                                   fiat=config.FIAT_MARKET,
                                   cryptos=cryptos)

        # Engine to Database
        self.engine = sqlalchemy.create_engine(f"sqlite:///{config.db_path}")

    def get_correct_fractional_part(self, symbol, number, price=True):
        """Get the step size for crypto currencies used by the api"""
        symbol_info = self.api.get_exchange_info(symbol)["symbols"][0]

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
        for balance in self.api.get_balance()["balances"]:
            if balance["asset"].lower() == self.portfolio.fiat:
                return float(balance["free"])

    # ----- SETUP FOR ORDERS ----- #

    def get_investment_amount(self):
        """Checks if there is any available currency in current balance to invest"""

        if self.portfolio.fiat_balance < 10:
            return

        active_balances = self.portfolio.get_active_balances_count()
        available_balances = len(self.portfolio.crypto_balances) - active_balances
        investment = self.portfolio.fiat_balance / available_balances
        if investment > 10:
            return investment

    def get_coins_to_buy(self, strategy):
        price = strategy.current_data["Price"].iloc[-1]
        fiat_amount = self.get_investment_amount()
        rounded_price = self.get_correct_fractional_part(symbol=strategy.symbol, number=price)

        if fiat_amount:
            crypto_coins = fiat_amount / rounded_price
            rounded_coins = self.get_correct_fractional_part(symbol=strategy.symbol, number=crypto_coins, price=False)
            if (rounded_coins * rounded_price) <= fiat_amount:
                return rounded_price, rounded_coins

    def get_coins_to_sell(self, symbol):
        """Checks if placing a sell order is warranted"""
        crypto = self.portfolio.query_crypto_balance(crypto=symbol)
        crypto_coins = crypto.balance
        return self.get_correct_fractional_part(symbol=symbol, number=crypto_coins, price=False)

    # ----- PLACE ORDERS ----- #

    def place_limit_order(self, price, symbol, action, crypto_coins):
        """Place limit order"""

        receipt = self.api.post_order(asset=symbol, action=action, order_type="limit", price=price,
                                      quantity_type="quantity", amount=crypto_coins)

        confirmation = self.api.query_order(asset_symbol=symbol, order_id=receipt["orderId"])

        for _ in range(5):
            if confirmation["status"].lower() == "filled":
                return confirmation
            else:
                time.sleep(5)
                confirmation = self.api.query_order(asset_symbol=symbol, order_id=receipt["orderId"])

        return self.api.cancel_orders(symbol=symbol)

    def process_order(self, receipt, strategy):
        crypto = self.portfolio.query_crypto_balance(receipt["symbol"].lower())
        self.portfolio.fiat_balance = self.balance_request()
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
                order.to_sql(engine=self.engine, stop_loss=stop_loss)
            else:
                order.to_sql(engine=self.engine)

            coins = float(receipt["executedQty"]) * 0.999
            value = float(receipt["price"]) * coins
            crypto.update(investment=investment, balance=coins, value=value)
        else:
            order.to_sql(engine=self.engine, buy_order_id=order.get_last_buy_order(engine=self.engine).order_id)
            crypto.update(investment=0, balance=0, value=0)

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
        new_balance = self.portfolio.fiat_balance
        first_line = f"{action.upper()} ORDER PLACED FOR {asset_symbol.upper()}"
        second_line = f"NEW BALANCE: {round(new_balance, 2)}"
        return first_line, second_line

    # ----- ON/OFF BUTTON ----- #

    def activate(self):
        """Activate the bot"""
        just_posted = False
        self.portfolio.fiat_balance = self.balance_request()

        while True:
            current_time = time.time()

            for strategy in self.strategies:

                # Checks for each strategy if new data can be retrieved
                if -1 <= (current_time % strategy.interval_1h[1]) <= 1:
                    time.sleep(10)

                    # Get data from binance and determine if action needs to be taken
                    new_data = self.api.get_history(symbol=strategy.symbol,
                                                    interval=strategy.interval_4h[0],
                                                    limit=200)
                    strategy.current_data_4h = new_data
                    self.print_new_data(df=strategy.current_data_4h, strategy=strategy)
                    action = strategy.check_for_bull_market()

                    if action == "check for opportunity":
                        new_data = self.api.get_history(symbol=strategy.symbol,
                                                        interval=strategy.interval_1h[0],
                                                        limit=14)
                        strategy.current_data_1h = new_data
                        self.print_new_data(df=strategy.current_data_1h, strategy=strategy)
                        action = strategy.check_for_opportunity()

                    if action is None:
                        continue

                    # Prepare and place order
                    price, crypto_coins = self.get_coins_to_buy(strategy=strategy)

                    if crypto_coins is None:
                        continue

                    order_receipt = self.place_limit_order(symbol=strategy.symbol,
                                                           price=price, action=action, crypto_coins=crypto_coins)

                    if order_receipt["status"].lower() == "filled":
                        self.process_order(receipt=order_receipt, strategy=strategy)
                        self.print_new_order(action, strategy.symbol)

                    just_posted = True

            # Bot can sleep. No new data has to be retrieved for a while
            if just_posted:
                time.sleep(3540)
                just_posted = False
