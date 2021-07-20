import pandas as pd
import pandas_ta as pta
import time
# import sqlalchemy
from trader import TraderAPI
from wallet import Portfolio
from strategies import *

MA1 = 50
MA2 = 200
SHORT_INTERVAL = "30m"
LONG_INTERVAL = "4h"
LOG_COLUMNS = ["Timestamp", "Asset", "Action", "Price", "Volume", "Strategy"]


def calculate_rsi(df_column, window=14):
    delta = df_column.diff(1)

    positives = delta.copy()
    negatives = delta.copy()
    positives[positives < 0] = 0
    negatives[negatives > 0] = 0

    rs = positives.rolling(window).mean() / abs(negatives.rolling(window).mean())
    rsi = 100 - 100 / (1 + rs)
    return rsi


def current_ms_time():
    return round(time.time() * 1000)


def create_dataframe(symbol, interval, limit):
    df = pd.DataFrame(trader.get_history(symbol, interval, limit=limit))
    df = df.drop(columns=df.iloc[:, 2:].columns)
    df.columns = ["Open Time", "Price"]
    df = df.set_index("Open Time")
    df.index = pd.to_datetime(df.index, unit="ms")
    df = df.astype(float)
    df[f"SMA_{MA1}"] = df["Price"].rolling(window=MA1).mean()
    df[f"SMA_{MA2}"] = df["Price"].rolling(window=MA2).mean()
    df["RSI"] = pta.rsi(df["Price"], length=14)
    return df


def process_order(trade, db_engine, strategy):
    entry = [trade["transactTime"], trade["symbol"], trade["side"], trade["price"], trade["executedQty"], strategy]
    log = pd.DataFrame([entry], columns=LOG_COLUMNS)
    log.to_sql("TradeLog", db_engine, if_exists="append", index=False)


def add_border(message):
    formatted_message = "<-------------------------" + message
    while len(formatted_message) < 92:
        formatted_message += "-"
    return formatted_message + ">"


def format_data_message(df, asset_symbol, strategy_type):
    print(add_border(f"RETRIEVING DATA FOR {asset_symbol} {strategy_type} TERM STRATEGY"))
    print(df.iloc[[-1]])
    print(add_border(""))


def format_order_message(order_action):
    print(add_border(f"{order_action} ORDER PLACED"))
    print(add_border(f"NEW BALANCE: {portfolio.balance}"))
    print(add_border(""))


trader = TraderAPI()
portfolio = Portfolio(trader)
crossing_sma = CrossingSMA(MA1, MA2)
bottom_rsi = BottomRSI(MA1, MA2)
# engine = sqlalchemy.create_engine("sqlite:///data/trade_log.db")

counter = 0
while True:

    current_time = current_ms_time()

    if (current_time / 1000) % 1800 == 0:
        time.sleep(30)

        for asset in portfolio.assets:
            df_asset_30m = create_dataframe(asset, SHORT_INTERVAL, MA2)

            format_data_message(df_asset_30m, asset, "SHORT")

            action = bottom_rsi.check_for_signal(df_asset_30m)

            if action == "BUY":
                if crossing_sma.buy:
                    order_price = round(portfolio.balance, 2)
                else:
                    order_price = round(portfolio.balance * 0.34, 2)

                receipt = trader.post_order(asset, order_price, action)

                # process_order(receipt, engine, "RSI buy")
                portfolio.coins[f"{asset} short term"] = round(float(receipt["origQty"]) * 0.992)
                portfolio.get_balance()

                format_order_message(action)

            elif action == "SELL":
                receipt = trader.post_order(asset, portfolio.coins[f"{asset} short term"], action)
                # process_order(receipt, engine, "RSI sell")
                portfolio.coins[f"{asset} short term"] = 0
                portfolio.get_balance()

                format_order_message(action)

            if counter % 8 == 0:
                df_asset_4h = create_dataframe(asset, LONG_INTERVAL, MA2)
                counter = 0

                format_data_message(df_asset_4h, asset, "LONG")

                action = crossing_sma.check_for_signal(df_asset_4h)

                if action == "BUY":
                    if bottom_rsi.buy:
                        order_price = round(portfolio.balance, 2)
                    else:
                        order_price = round(portfolio.balance * 0.66, 2)

                    receipt = trader.post_order(asset, order_price, action)
                    # process_order(receipt, engine, "Golden cross")
                    portfolio.coins[f"{asset} long term"] = round(float(receipt["origQty"]) * 0.992)
                    portfolio.get_balance()

                    format_order_message(action)

                elif action == "SELL":
                    receipt = trader.post_order(asset, portfolio.coins[f"{asset} long term"], action)
                    # process_order(receipt, engine, "Death cross")
                    portfolio.coins[f"{asset} long term"] = 0
                    portfolio.get_balance()

                    format_order_message(action)

        time.sleep(60)
        counter += 1

# TODO: Give strategies a type attribute, add every strategy instance to a list and loop through it for better
#  efficiency in the code

# TODO: Find solution for currency issue
