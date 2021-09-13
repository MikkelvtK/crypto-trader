import sqlalchemy
from decorators import *
from functions import *
from constants import *
from database import *
from strategies import TrailingStopLoss
from sqlalchemy.orm import sessionmaker


class TraderBot:

    def __init__(self, name, api, strategies, fiat_market):

        # Setup up all parameters given
        self.name = name
        self.api = api
        self.strategies = strategies
        self.fiat_market = fiat_market

        # Connect to Database
        self.engine = sqlalchemy.create_engine(f"sqlite:///{config.db_path}")
        self.session = sessionmaker(self.engine)

        # Initialising all data from databases and Binance account
        self.active_investments = self.set_active_investments()
        self.current_balance = self.set_balance()
        self.total_budget = self.set_balance()
        self.available_to_invest = self.calculate_available_budget()
        self.active_stop_losses = {}
        self.set_active_stop_losses()

    # ----- UPDATE ATTRIBUTES ----- #

    def update_attributes(self):
        """Update active_investments, current_balance, total_budget and available_to_invest attributes of bot"""
        self.active_investments = self.set_active_investments()
        self.current_balance = self.set_balance()
        self.total_budget = self.calculate_budget()
        self.available_to_invest = self.calculate_available_budget()

    def set_active_investments(self):
        """Sets which assets are currently active for the strategy"""
        return pd.read_sql("active_trades", self.engine)

    def set_balance(self):
        """Get float value of total balance (available and currently invested)"""
        for balance in self.api.get_balance()["balances"]:
            if balance["asset"].lower() == self.fiat_market:
                return float(balance["free"])

    def calculate_budget(self):
        """Add current balance to the amount that is currently invested to get a total budget."""
        return self.current_balance + self.active_investments["investment"].sum()

    def calculate_available_budget(self):
        """Calculates available budget for investment for different types of trading."""

        # Determine what part of the budget is currently invested
        active_hodl = self.active_investments.loc[self.active_investments["type"] == "long", "investment"].sum()
        active_day_trading = self.active_investments.loc[self.active_investments["type"] == "short", "investment"].sum()
        ratio = active_hodl / self.total_budget

        # Calculate what part of the budget is still available to invest
        available_budget_dict = {
            "available hodl budget": self.total_budget * 0.6 - active_hodl,
            "available day trading budget": self.total_budget * 0.4 - active_day_trading,
        }

        # Adjust budget for day trading if not enough is available
        if ratio > 0.6:
            available_budget_dict["available day trading budget"] = self.current_balance

        if available_budget_dict["available hodl budget"] < 0:
            available_budget_dict["available hodl budget"] = 0

        return available_budget_dict

    def set_active_stop_losses(self):
        """Read active stop losses when starting the bot"""

        for strategy in self.strategies:
            self.active_stop_losses[strategy.name] = {}

        df = pd.read_sql("stop_losses", self.engine)

        if not df.empty:
            for index, row in df.iterrows():
                stop_loss = TrailingStopLoss(row["strategy_name"], row["asset"], row["highest"])
                self.active_stop_losses[stop_loss.strategy_name][stop_loss.asset] = stop_loss

    # ----- DATA HANDLING ----- #

    def retrieve_usable_data(self, asset_symbol, strategy):
        """Get new data from binance API and manipulate to usable data."""
        new_data = self.api.get_history(symbol=asset_symbol, interval=strategy.interval[0], limit=MA2)
        df = create_dataframe(new_data)
        self.print_new_data(df, asset_symbol.upper(), strategy)
        return df

    # ----- ANALYSING DATA ----- #

    def analyse_new_data(self, df, asset_symbol, strategy):
        """Analyse the data to decide if any action needs to be taken"""

        # Determine if an investment is currently active for the crypto coin
        active_trades = self.active_investments.loc[self.active_investments["strategy"] == strategy.name]
        if asset_symbol in active_trades["asset"].values:
            active = True
        else:
            active = False

        kwargs = {"dataframe": df, "active": active, "stop_loss": None}

        # Adjust and update the trailing stop loss if asset is active
        if strategy.trailing_stop_loss and active:
            stop_loss = self.active_stop_losses[strategy.name][asset_symbol]
            stop_loss.adjust_stop_loss(df["Price"].iloc[-1])
            self.update_stop_loss(stop_loss)
            kwargs["stop_loss"] = stop_loss

        return strategy.check_for_signal(**kwargs)

    # ----- SETUP FOR ORDERS ----- #

    def prepare_order(self, asset_symbol, strategy, action):
        """Prepare variables to place order"""
        if action == "buy":
            return self.determine_investment_amount(strategy)

        if action == "sell" or action == "quick sell":
            return self.retrieve_coins(asset_symbol, strategy)

    def determine_investment_amount(self, strategy):
        """Checks if there is any available currency in current balance to invest"""
        if self.current_balance < 10:
            return None

        long = self.active_investments.loc[self.active_investments["type"] == "long"]
        short = self.active_investments.loc[self.active_investments["type"] == "short"]

        # The check for long investments
        if strategy.type == "long":
            active_assets = long["type"].count()
            available_assets = len(strategy.assets) - active_assets
            investment = self.available_to_invest["available hodl budget"] / available_assets
            rounded_investment = calc_correct_quantity(3, investment)
            if rounded_investment > 10:
                return rounded_investment

        # The check for short investments
        elif strategy.type == "short" and short["type"].count() < 2:
            modifier = 0.5
            if short["type"].count() == 1:
                modifier = 1

            investment = self.available_to_invest["available day trading budget"] * modifier
            rounded_investment = calc_correct_quantity(3, investment)
            if rounded_investment > 10:
                return rounded_investment

    def retrieve_coins(self, asset_symbol, strategy):
        """Checks if placing a sell order is warranted"""
        active_trades = self.active_investments.loc[self.active_investments["strategy"] == strategy.name]
        if asset_symbol in active_trades["asset"].values:
            coins = float(active_trades.loc[active_trades["asset"] == asset_symbol, "coins"])
            asset_step_size = self.get_step_size(asset_symbol)
            return calc_correct_quantity(asset_step_size, coins)
        return None

    # ----- CHECKS FOR CONDITIONS ----- #

    def update_long_investment(self, asset_symbol, strategy):
        """Checks if there is any balance available to put in long investments"""
        pass

    def get_step_size(self, asset_symbol):
        """Retrieve how many decimal points are allowed by the API for the currency."""
        symbol_info = self.api.get_exchange_info(asset_symbol.upper())["symbols"][0]
        lot_size_filter = symbol_info["filters"][2]
        step_size = lot_size_filter["stepSize"].find("1") - 1
        return step_size

    def get_tick_size(self, asset_symbol):
        symbol_info = self.api.get_exchange_info(asset_symbol.upper())["symbols"][0]
        lot_size_filter = symbol_info["filters"][0]
        tick_size = lot_size_filter["tickSize"].find("1") - 1
        return tick_size

    # ----- PLACE ORDERS ----- #

    def place_order(self, asset_symbol, order_quantity, action):
        """Place the order based on the action."""

        if action == "buy":
            manner = "quoteOrderQty"
        else:
            manner = "quantity"

        receipt = self.api.post_order(asset=asset_symbol.upper(), quantity=order_quantity,
                                      order_type=manner, action=action.upper())
        if receipt["status"].lower() == "filled":
            return receipt

    def place_limit_order(self, asset_symbol, df, order_quantity, action):
        price = df["Price"].iloc[-1]
        correct_price = calc_correct_quantity(self.get_tick_size(asset_symbol), price)
        asset_step_size = self.get_step_size(asset_symbol)

        if action == "buy":
            order_quantity = calc_correct_quantity(asset_step_size, order_quantity / correct_price)

        receipt = self.api.post_order(asset=asset_symbol, action=action, order_type="limit", price=correct_price*0.999,
                                      quantity_type="quantity", amount=order_quantity)

        if receipt["status"].lower() == "filled":
            return receipt

    # ----- LOGGING ORDERS ----- #

    # ORDERS #
    def log_buy_order(self, asset_symbol, coins, investment, strategy):
        """Saves active orders to load when restarting."""
        with self.session() as new_session:
            new_buy_order = TradeLog(
                asset=asset_symbol,
                coins=coins,
                investment=investment,
                strategy=strategy.name,
                type=strategy.type
            )

            new_session.add(new_buy_order)
            new_session.commit()

    def delete_sold_order(self, asset_symbol, strategy):
        """Delete buy order from database when asset is sold."""
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("active_trades", metadata, autoload_with=self.engine)
        action_to_execute = table.delete().where(table.columns.asset == asset_symbol,
                                                 table.columns.strategy == strategy.name)
        with self.engine.connect() as connection:
            connection.execute(action_to_execute)

    def update_long_trade(self, asset_symbol, coins, investment, strategy):
        """Update database with any changes in trade"""
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("active_trades", metadata, autoload_with=self.engine)
        db_update = sqlalchemy.update(table).where(table.columns.strategy == strategy.name,
                                                   table.columns.asset == asset_symbol).\
            values(coins=coins, investment=investment)

        with self.engine.connect() as connection:
            connection.execute(db_update)

    # TRAILING STOP LOSS #
    def log_stop_loss(self, stop_loss):
        """Save a newly activated trailing stop loss"""
        with self.session() as new_session:
            new_stop_loss = StopLoss(
                strategy_name=stop_loss.strategy_name,
                asset=stop_loss.asset,
                highest=stop_loss.highest,
                trail=stop_loss.trail
            )

            new_session.add(new_stop_loss)
            new_session.commit()

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

            for strategy in self.strategies:

                # Checks for each strategy if new data can be retrieved
                if -1 <= (current_time % strategy.interval[1]) <= 1:
                    time.sleep(15)

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
                            order_receipt = self.place_limit_order(asset_symbol=asset, df=new_df,
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
