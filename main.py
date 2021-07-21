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
portfolio = Portfolio(trader.get_balance())
crossing_sma = CrossingSMA(MA1, MA2, interval=("4h", 14400), strategy_type="LONG", balance=portfolio.balance * 0.66)
bottom_rsi = BottomRSI(interval=("30m", 1800), strategy_type="SHORT", balance=portfolio.balance * 0.34)
strategies = (crossing_sma, bottom_rsi)
# engine = sqlalchemy.create_engine("sqlite:///data/trade_log.db")

just_posted = False
while True:
    current_time = current_ms_time()

    for strategy in strategies:

        if -1 <= ((current_time / 1000) % strategy.interval[1]) <= 1:
            time.sleep(15)

            for asset in portfolio.assets:
                df_asset = create_dataframe(asset, strategy.interval[0], MA2)

                format_data_message(df_asset, asset, strategy.strategy_type)

                action = strategy.check_for_signal(df_asset)

                if action == "BUY":
                    key = f"{asset} {strategy.strategy_type.lower()} term"
                    receipt = trader.post_order(asset, round(strategy.usable_balance, 2), action)
                    if receipt["status"] == "FILLED":
                        strategy.buy = True

                        # process_order(receipt, engine, "RSI buy")
                        quantity = round(float(receipt["origQty"]))
                        portfolio.coins[key] = quantity
                        portfolio.balance = trader.get_balance()

                        format_order_message(action)

                elif action == "SELL":
                    key = f"{asset} {strategy.strategy_type.lower()} term"
                    receipt = trader.post_order(asset, (portfolio.coins[key] * df_asset["Price"].iloc[-1]), action)

                    if receipt["status"] == "FILLED":
                        strategy.buy = False

                        # process_order(receipt, engine, "RSI sell")
                        portfolio.coins[key] = 0
                        portfolio.balance = trader.get_balance()
                        strategy.usable_balance = round(receipt["origQty"] * receipt["price"], 2)
                        format_order_message(action)

            just_posted = True

    if just_posted:
        time.sleep(60)
        just_posted = False
