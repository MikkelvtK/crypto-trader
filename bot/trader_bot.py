import sqlalchemy
import bot.config as config
from decorators import *
from functions import *
from constants import *
from database import *
from bot.class_blueprints.stop_loss import TrailingStopLoss
from bot.class_blueprints.trader import TraderAPI
from bot.class_blueprints.crypto import Crypto
from bot.class_blueprints.portfolio import Portfolio


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

    def get_coins_to_buy(self, crypto_price, investment):
        pass

    def get_coins_to_sell(self, symbol):
        """Checks if placing a sell order is warranted"""
        crypto = self.portfolio.query_crypto_balance(crypto=symbol)
        crypto_coins = crypto.balance
        rounded_crypto_coins = self.get_correct_fractional_part(symbol=symbol, number=crypto_coins, price=False)
        return rounded_crypto_coins

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

    # ----- VISUAL FEEDBACK ----- #

    @add_border
    def print_new_data(self, df, asset_symbol, strategy):
        """Print new data result"""
        message = f"RETRIEVING DATA FOR {asset_symbol.upper()} {strategy.name.upper()} STRATEGY"
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

        while True:
            current_time = time.time()
            time.sleep(5)

            for strategy in self.strategies:

                # Checks for each strategy if new data can be retrieved
                if -1 <= (current_time % strategy.interval[1]) <= 1:
                    time.sleep(10)

                    # Get data from binance and determine if action needs to be taken
                    new_data = self.api.get_history(symbol=strategy.symbol,
                                                    interval=strategy.interval,
                                                    limit=strategy.limit)
                    strategy.current_data = new_data
                    action = strategy.check_for_signal()

                    if action is None:
                        continue

                    # Prepare and place order
                    price = strategy.current_data["Price"].iloc[-1]
                    fiat_amount = self.get_investment_amount()
                    rounded_price = self.get_correct_fractional_part(symbol=strategy.symbol, number=price)
                    crypto_coins = fiat_amount / rounded_price

                    if crypto_coins is None:
                        continue
                    elif action == "quick sell":
                        order_receipt = self.place_order(asset_symbol=asset, order_quantity=quantity, action="sell")
                    else:
                        order_receipt = self.place_limit_order(asset_symbol=asset,
                                                               order_quantity=quantity, action=action)

                    if order_receipt:

                        # If order is placed, update and log all attributes
                        new_coins = float(order_receipt["executedQty"]) * 0.999
                        if action == "buy":
                            self.log_buy_order(asset_symbol=asset, coins=new_coins,
                                               investment=quantity, strategy=strategy)
                            if strategy.trailing_stop_loss:
                                stop_loss = TrailingStopLoss(strategy.name, asset, strategy.current_price)
                                self.active_stop_losses[strategy.name][asset] = stop_loss
                                self.log_stop_loss(stop_loss)
                        else:
                            self.delete_sold_order(asset_symbol=asset, strategy=strategy)
                            if strategy.trailing_stop_loss:
                                self.delete_stop_loss(stop_loss=self.active_stop_losses[strategy.name][asset])
                                del self.active_stop_losses[strategy.name][asset]

                        self.update_attributes()
                        self.print_new_order(action, asset)

                    just_posted = True

            # Bot can sleep. No new data has to be retrieved for a while
            if just_posted:
                time.sleep(1740)
                just_posted = False
