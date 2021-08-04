import pandas as pd
import sqlalchemy
from decorators import *

MA1 = 40
MA2 = 170


class TraderBot:

    def __init__(self, name, api, strategies):
        self.name = name
        self.api = api
        self.strategies = strategies
        self.engine = sqlalchemy.create_engine(f"sqlite:///{config.db_path}")
        self.total_balance = self.set_current_balance()
        self.active_investments = self.set_active_investments()
        self.available_to_invest = self.set_available_investments()

    def set_active_investments(self):
        """Sets which assets are currently active for the strategy"""
        df = pd.read_sql("active_trades", self.engine)
        df = df.set_index("asset")
        return df

    def set_current_balance(self):
        """Get float value of spendable currency"""
        for balance in self.api.get_balance()["balances"]:
            if balance["asset"].lower() == "eur":
                return float(balance["free"]) + self.active_investments["investment"].sum()

    def set_available_investments(self):
        available_dict = {
            "available long": self.total_balance * 0.6 - self.active_investments.loc[
                self.active_investments["type"] == "long", ["investment"]].sum(),
            "available short": self.total_balance * 0.4 - self.active_investments.loc[
                self.active_investments["type"] == "short", ["investment"]].sum(),
        }
        return available_dict

    def place_buy_order(self, strategy, asset):
        if strategy.type == "long":
            active_assets = self.active_investments[self.active_investments["type"] == "long"].count()
            available_assets = len(strategy.assets) - active_assets
            investment = round(self.available_to_invest["available long"] / available_assets, 2)
        else:
            investment = round(self.available_to_invest["available short"], 2)
        receipt = self.api.post_order(asset=asset, quantity=investment, action="quoteOrderQty")
        if receipt["status"].lower() == "filled":
            return receipt

    def place_sell_order(self, strategy, asset):
        pass

    @add_border
    def print_new_data(self, df, symbol, strategy):
        """Print new data result"""
        message = f"RETRIEVING DATA FOR {symbol.upper()} {strategy.name} STRATEGY"
        data = [f"{index:<15}{item}" for index, item in df.iloc[-1, :].items()]
        return data.insert(0, message)

    @add_border
    def print_new_order(self, action, symbol):
        """Print when order is placed"""
        new_balance = self.total_balance - self.active_investments["investment"].sum()
        first_line = f"{action.upper()} ORDER PLACED FOR {symbol.upper()}"
        second_line = f"NEW BALANCE: {new_balance}"
        return first_line, second_line

    def activate(self):
        current_time = time.time()

        for strategy in self.strategies:

            if -1 <= (current_time % strategy.interval[1]) <= 1:
                time.sleep(15)

                for asset in strategy.assets:
                    new_df = create_dataframe(asset, strategy.interval[0], MA2)






















