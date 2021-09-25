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
        symbol_info = self.api.get_exchange_info(symbol.upper())["symbols"][0]

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

    def prepare_order(self, asset_symbol, strategy, action):
        """Prepare variables to place order"""
        if action == "buy":
            return self.get_investment_amount()

        if action == "sell" or action == "quick sell":
            return self.retrieve_coins(asset_symbol, strategy)

    def get_investment_amount(self):
        """Checks if there is any available currency in current balance to invest"""

        if self.portfolio.fiat_balance < 10:
            return

        active_balances = self.portfolio.get_active_balances_count()
        available_balances = len(self.portfolio.crypto_balances) - active_balances
        investment = self.portfolio.fiat_balance / available_balances
        if investment > 10:
            return investment

    #TODO: Get crypto currency to sell from active balance
    def retrieve_coins(self, asset_symbol, strategy):
        """Checks if placing a sell order is warranted"""
        active_trades = self.active_investments.loc[self.active_investments["strategy"] == strategy.name]
        if asset_symbol in active_trades["asset"].values:
            coins = float(active_trades.loc[active_trades["asset"] == asset_symbol, "coins"])
            asset_step_size = self.get_step_size(asset_symbol)
            return calc_correct_quantity(asset_step_size, coins)

    # ----- CHECKS FOR CONDITIONS ----- #

    def update_long_investment(self, asset_symbol, strategy):
        """Checks if there is any balance available to put in long investments"""
        pass

    # ----- PLACE ORDERS ----- #

    def place_order(self, asset_symbol, order_quantity, action):
        """Place the order based on the action."""

        if action == "buy":
            manner = "quoteOrderQty"
        else:
            manner = "quantity"

        receipt = self.api.post_order(asset=asset_symbol, amount=order_quantity, quantity_type=manner,
                                      order_type="market", action=action)
        if receipt["status"].lower() == "filled":
            return receipt

    def place_limit_order(self, asset_symbol, order_quantity, action):
        """Place limit order"""
        price = float(self.api.get_latest_price(asset=asset_symbol)["price"])
        asset_step_size = self.get_step_size(asset_symbol)

        if action == "buy":
            price *= 1.001
            order_quantity = calc_correct_quantity(asset_step_size, order_quantity / price)
        else:
            price *= 0.999

        new_price = calc_correct_quantity(self.get_tick_size(asset_symbol), price)
        receipt = self.api.post_order(asset=asset_symbol, action=action, order_type="limit", price=new_price,
                                      quantity_type="quantity", amount=order_quantity)

        confirmation = self.api.query_order(asset_symbol=asset_symbol, order_id=receipt["orderId"])

        while not confirmation["status"].lower() == "filled":
            time.sleep(5)
            confirmation = self.api.query_order(asset_symbol=asset_symbol, order_id=receipt["orderId"])
        return confirmation

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
        new_balance = self.total_budget - self.active_investments["investment"].sum()
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

                    for asset in strategy.assets:

                        # Get data from binance and determine if action needs to be taken
                        new_df = self.retrieve_usable_data(asset_symbol=asset, strategy=strategy)
                        action = self.analyse_new_data(df=new_df, asset_symbol=asset, strategy=strategy)

                        if action is None:
                            continue

                        # Prepare and place order
                        quantity = self.prepare_order(asset_symbol=asset, strategy=strategy, action=action)

                        if quantity is None:
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
