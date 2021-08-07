import sqlalchemy
from decorators import *
from functions import *
from constants import *
from strategies import TrailingStopLoss


class TraderBot:

    def __init__(self, name, api, strategies):
        self.name = name
        self.api = api
        self.strategies = strategies
        self.engine = sqlalchemy.create_engine(f"sqlite:///{config.db_path}")
        self.active_investments = self.set_active_investments()
        self.total_balance = self.set_current_balance()
        self.available_to_invest = self.set_available_investments()
        self.active_stop_losses = []

    # ----- UPDATE ATTRIBUTES ----- #

    def set_active_investments(self):
        """Sets which assets are currently active for the strategy"""
        df = pd.read_sql("active_trades", self.engine)
        return df

    def set_current_balance(self):
        """Get float value of total balance (available and currently invested)"""
        for balance in self.api.get_balance()["balances"]:
            if balance["asset"].lower() == "eur":
                return float(balance["free"]) + self.active_investments["investment"].sum()

    def set_available_investments(self):
        """Divides the available balance for short and long investments"""
        available_dict = {
            "available long": self.total_balance * 0.6 - self.active_investments.loc[
                self.active_investments["type"] == "long", ["investment"]].sum(),
            "available short": self.total_balance * 0.4 - self.active_investments.loc[
                self.active_investments["type"] == "short", ["investment"]].sum(),
        }
        return available_dict

    # ----- CHECKS FOR CONDITIONS ----- #

    def is_asset_active(self, strategy, asset_symbol):
        """Checks if the asset already has an active investment for the strategy"""
        active_trades = self.active_investments.loc[self.active_investments["strategy"] == strategy.name]
        if asset_symbol in active_trades["asset"].values:
            return True
        return False

    def check_available_balance(self, strategy):
        """Checks if there is any available currency in current balance to invest"""
        long = self.active_investments.loc[self.active_investments["type"] == "long"]
        short = self.active_investments.loc[self.active_investments["type"] == "short"]

        # The check for long investments
        if strategy.type == "long":
            active_assets = long["type"].count()
            available_assets = len(strategy.assets) - active_assets
            return float(round(self.available_to_invest["available long"] / available_assets, 2))

        # The check for short investments
        elif strategy.type == "short" and short["type"].count() < 2:
            modifier = 0.5
            if short["type"].count() == 1:
                modifier = 1
            return float(round(self.available_to_invest["available short"] * modifier, 2))

        return False

    def check_sell_order(self, asset_symbol, strategy):
        """Checks if placing a sell order is warranted"""
        active_trades = self.active_investments.loc[self.active_investments["strategy"] == strategy.name]
        if asset_symbol in active_trades["asset"].values:
            return float(active_trades.loc[active_trades["asset"] == asset_symbol, "coins"])
        return False

    # ----- PLACE ORDERS ----- #

    def place_buy_order(self, asset_symbol, investment):
        """Places buy order for the API"""
        receipt = self.api.post_order(asset=asset_symbol.upper(), quantity=investment,
                                      manner="quoteOrderQty", action="BUY")
        if receipt["status"].lower() == "filled":
            return True, receipt
        return False, None

    def place_sell_order(self, asset_symbol, coins):
        """Places sell order for the API"""
        order_quantity = calc_true_order_quantity(self.api, asset_symbol.upper(), coins)
        receipt = self.api.post_order(asset=asset_symbol.upper(), quantity=order_quantity,
                                      manner="quantity", action="SELL")
        if receipt["status"].lower() == "filled":
            return True
        return False

    # ----- VISUAL FEEDBACK ----- #

    @add_border
    def print_new_data(self, df, asset_symbol, strategy):
        """Print new data result"""
        message = f"RETRIEVING DATA FOR {asset_symbol.upper()} {strategy.name.upper()} STRATEGY"
        data = [f"{index:<15}{round(item, 4)}" for index, item in df.iloc[-1, :].items()]
        return [message] + data

    @add_border
    def print_new_order(self, action, asset_symbol):
        """Print when order is placed"""
        new_balance = self.total_balance - self.active_investments["investment"].sum()
        first_line = f"{action.upper()} ORDER PLACED FOR {asset_symbol.upper()}"
        second_line = f"NEW BALANCE: {round(new_balance, 2)}"
        return first_line, second_line

    # ----- DATABASE ----- #

    # ORDERS #
    def log_buy_order(self, asset_symbol, coins, investment, strategy):
        """Saves active orders to load when restarting."""
        row = {"asset": [asset_symbol], "coins": [coins], "investment": [investment],
               "strategy": [strategy.name], "type": [strategy.type]}
        df = pd.DataFrame(row)
        df.to_sql("active_trades", self.engine, if_exists="append", index=False)

    def delete_sold_order(self, asset_symbol, strategy):
        """Delete buy order from database when asset is sold."""
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("active_trades", metadata, autoload_with=self.engine)
        action_to_execute = table.delete().where(table.columns.asset == asset_symbol,
                                                 table.columns.strategy == strategy.name)
        with self.engine.connect() as connection:
            connection.execute(action_to_execute)

    # TRAILING STOP LOSS #
    def log_stop_loss(self, stop_loss):
        """Save a newly activated trailing stop loss"""
        row = {"strategy_name": [stop_loss.strategy_name], "asset": [stop_loss.asset], "highest": [stop_loss.highest],
               "trail": [stop_loss.trail]}
        df = pd.DataFrame(row)
        df.to_sql("stop_losses", self.engine, if_exists="append", index=False)

    def update_stop_loss(self, stop_loss):
        """Update any changes to the trailing stop loss in the database"""
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("stop_losses", metadata, autoload_with=self.engine)

        db_update = sqlalchemy.update(table).where(table.columns.strategy_name == stop_loss.strategy_name,
                                                   table.columns.asset == stop_loss.asset).\
            values(highest=stop_loss.highest, trail=stop_loss.trail)

        with self.engine.connect() as connection:
            connection.execute(db_update)

    def delete_stop_loss(self, stop_loss):
        """Delete trailing stop loss if asset is sold"""
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("stop_losses", metadata, autoload_with=self.engine)
        action_to_execute = table.delete().where(table.columns.strategy_name == stop_loss.strategy_name,
                                                 table.columns.asset == stop_loss.asset)
        with self.engine.connect() as connection:
            connection.execute(action_to_execute)

    # ----- ON/OFF BUTTON ----- #

    def activate(self):
        """Activate the bot"""
        just_posted = False

        while True:
            current_time = time.time()

            for strategy in self.strategies:

                # Checks for each strategy if new data can be retrieved
                if -1 <= (current_time % strategy.interval[1]) <= 1:
                    time.sleep(15)

                    for asset in strategy.assets:

                        # Retrieve, print and analyse new data
                        new_df = create_dataframe(self.api, asset.upper(), strategy.interval[0], MA2)
                        self.print_new_data(new_df, asset, strategy)
                        is_active = self.is_asset_active(strategy, asset)
                        action = strategy.check_for_signal(new_df, is_active, asset_symbol=asset)

                        # Update active trailing stop loss
                        if strategy.trailing_stop_loss:
                            for stop_loss in strategy.active_stop_losses:
                                if stop_loss.asset == asset:
                                    self.update_stop_loss(stop_loss)

                        if action == "buy":

                            # Sets the amount that will be invested
                            investment = self.check_available_balance(strategy)

                            if investment is False:
                                continue

                            asset_bought, order_receipt = self.place_buy_order(asset, investment)

                            # If asset bought, adjust all bot attributes and print action
                            if asset_bought:
                                bought_coins = float(order_receipt["executedQty"]) * 0.999
                                self.log_buy_order(asset, bought_coins, investment, strategy)
                                self.active_investments = self.set_active_investments()
                                self.available_to_invest = self.set_available_investments()
                                self.print_new_order(action, asset)

                                # Set trailing stop loss if strategy uses it
                                if strategy.trailing_stop_loss:
                                    stop_loss = TrailingStopLoss(strategy.name, asset, strategy.current_price)
                                    strategy.active_stop_losses.append(stop_loss)
                                    self.log_stop_loss(stop_loss)

                        if action == "sell":

                            # Retrieve the amount of coins to sell
                            coins_for_sale = self.check_sell_order(asset, strategy)

                            if coins_for_sale is False:
                                continue

                            asset_sold = self.place_sell_order(asset, coins_for_sale)

                            # If asset is sold, adjust all bot attributes and print action
                            if asset_sold:
                                self.delete_sold_order(asset, strategy)
                                self.active_investments = self.set_active_investments()
                                self.total_balance = self.set_current_balance()
                                self.available_to_invest = self.set_available_investments()
                                self.print_new_order(action, asset)

                                # Remove trailing stop loss if strategy uses it
                                if strategy.trailing_stop_loss:
                                    for stop_loss in strategy.active_stop_losses:
                                        if stop_loss.asset == asset:
                                            strategy.active_stop_losses.remove(stop_loss)
                                            self.delete_stop_loss(stop_loss)

                    just_posted = True

            # Bot can sleep. No new data has to be retrieved for a while
            if just_posted:
                time.sleep(720)
                just_posted = False
