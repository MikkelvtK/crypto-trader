import sqlalchemy
from decorators import *
from functions import *
from strategies import TrailingStopLoss

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
        self.active_stop_losses = []

    def set_active_investments(self):
        """Sets which assets are currently active for the strategy"""
        df = pd.read_sql("active_trades", self.engine)
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

    def check_available_balance(self, strategy, asset):
        long = self.active_investments.loc[self.active_investments["type"] == "long"]
        short = self.active_investments.loc[self.active_investments["type"] == "short"]
        if strategy.type == "long" and asset not in long["asset"].values:
            active_assets = long["type"].count()
            available_assets = len(strategy.assets) - active_assets
            available_balance = round(self.available_to_invest["available long"] / available_assets, 2)
        elif strategy.type == "short" and short["type"].count() < 2 and asset not in short["asset"].values:
            modifier = 0.5
            if short["type"].count() == 1:
                modifier = 1
            available_balance = round(self.available_to_invest["available short"] * modifier, 2)
        else:
            available_balance = 0
        return available_balance

    def check_sell_order(self, symbol, strategy):
        active_trades = self.active_investments.loc[self.active_investments["strategy"] == strategy.name]
        if symbol in active_trades["asset"].values:
            coins_for_sale = float(active_trades.loc[symbol, "coins"])
            return coins_for_sale
        return 0

    def place_buy_order(self, symbol):
        receipt = self.api.post_order(asset=symbol.upper(), quantity=5, manner="quoteOrderQty", action="BUY")
        if receipt["status"].lower() == "filled":
            return True, receipt
        return False, None

    def place_sell_order(self, symbol, coins):
        order_quantity = calc_true_order_quantity(self.api, symbol.upper(), coins)
        receipt = self.api.post_order(asset=symbol.upper(), quantity=order_quantity, manner="quantity", action="SELL")
        if receipt["status"].lower() == "filled":
            return True
        return False

    @add_border
    def print_new_data(self, df, symbol, strategy):
        """Print new data result"""
        message = f"RETRIEVING DATA FOR {symbol.upper()} {strategy.name.upper()} STRATEGY"
        data = [f"{index:<15}{item}" for index, item in df.iloc[-1, :].items()]
        return data.insert(0, message)

    @add_border
    def print_new_order(self, action, symbol):
        """Print when order is placed"""
        new_balance = self.total_balance - self.active_investments["investment"].sum()
        first_line = f"{action.upper()} ORDER PLACED FOR {symbol.upper()}"
        second_line = f"NEW BALANCE: {new_balance}"
        return first_line, second_line

    def log_buy_order(self, symbol, coins, investment, strategy):
        """Saves active orders to load when restarting."""
        row = {"asset": [symbol], "coins": [coins], "investment": [investment],
               "strategy": [strategy.name], "type": [strategy.type]}
        df = pd.DataFrame(row)
        df.to_sql("active_trades", self.engine, if_exists="append", index=False)

    def delete_buy_order(self, symbol, strategy):
        """Delete buy order from database when asset is sold."""
        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table("active_trades", metadata, autoload_with=self.engine)
        action_to_execute = table.delete().where(table.columns.asset == symbol,
                                                 table.columns.strategy == strategy.name)
        with self.engine.connect() as connection:
            connection.execute(action_to_execute)

    def activate(self):
        just_posted = False

        while True:
            current_time = time.time()

            for strategy in self.strategies:

                if -1 <= (current_time % strategy.interval[1]) <= 1:
                    time.sleep(15)

                    for asset in strategy.assets:

                        new_df = create_dataframe(self.api, asset.upper(), strategy.interval[0], MA2)
                        self.print_new_data(new_df, asset, strategy)
                        action = strategy.check_for_signal(new_df, asset)

                        if action == "buy":

                            investment = self.check_available_balance(strategy, asset)

                            if investment == 0:
                                continue

                            asset_bought, order_receipt = self.place_buy_order(asset)

                            if asset_bought:
                                bought_coins = float(order_receipt["executedQty"]) * 0.999
                                self.log_buy_order(asset, bought_coins, investment, strategy)
                                self.available_to_invest = self.set_available_investments()
                                self.print_new_order(action, asset)

                                if strategy.trailing_stop_loss:
                                    stop_loss = TrailingStopLoss(asset, strategy.current_price)
                                    strategy.active_stop_losses.append(stop_loss)

                        if action == "sell":

                            coins_for_sale = self.check_sell_order(asset, strategy)

                            if coins_for_sale == 0:
                                continue

                            asset_sold = self.place_sell_order(asset, coins_for_sale)

                            if asset_sold:
                                self.delete_buy_order(asset, strategy)
                                self.total_balance = self.set_current_balance()
                                self.active_investments = self.set_active_investments()
                                self.available_to_invest = self.set_available_investments()
                                self.print_new_order(action, asset)

                                if strategy.trailing_stop_loss:
                                    for stop_loss in strategy.active_stop_losses:
                                        if stop_loss == asset:
                                            strategy.active_stop_losses.remove(stop_loss)

                    just_posted = True

            if just_posted:
                time.sleep(60)
                just_posted = False
