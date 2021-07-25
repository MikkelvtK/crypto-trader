import pandas as pd
import pandas_ta as pta
import time
from trader import TraderAPI
from wallet import Portfolio
from strategies import *

MA1 = 40
MA2 = 170
STD = 20
M30 = ("30m", 1800)
M15 = ("15m", 900)
H4 = ("4h", 14400)
H1 = ("1h", 3600)
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
    df = pd.DataFrame(trader.get_history(0, symbol=symbol, interval=interval, limit=limit))
    df = df.drop(columns=df.iloc[:, 2:].columns)
    df.columns = ["Open Time", "Price"]
    df = df.set_index("Open Time")
    df.index = pd.to_datetime(df.index, unit="ms")
    df = df.astype(float)
    df[f"SMA_{MA1}"] = df["Price"].rolling(window=MA1).mean()
    df[f"SMA_{MA2}"] = df["Price"].rolling(window=MA2).mean()
    df["Std"] = df["Price"].rolling(window=STD).std()
    df["Upper"] = df[f"SMA_{MA1}"] + 1.5 * df["Std"]
    df["Lower"] = df[f"SMA_{MA1}"] - 2.5 * df["Std"]
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
    print(add_border(f"RETRIEVING DATA FOR {asset_symbol} {strategy_type} STRATEGY"))
    print(df.iloc[[-1]])
    print(add_border(""))


def format_order_message(order_action, active_asset):
    print(add_border(f"{order_action} ORDER PLACED FOR {active_asset}"))
    print(add_border(f"NEW BALANCE: {portfolio.balance}"))
    print(add_border(""))


trader = TraderAPI()
portfolio = Portfolio(trader.get_balance(0, asset="EUR"))
crossing_sma = CrossingSMA(MA1, MA2, interval=H4, strategy_type="LONG", balance=0.50)
bottom_rsi = BottomRSI(interval=H1, strategy_type="SHORT RSI", balance=0.25)
bollinger = BollingerBands(interval=M15, strategy_type="SHORT BOL", balance=0.25)
strategies = (crossing_sma, bottom_rsi, bollinger)

just_posted = False
while True:
    current_time = current_ms_time()

    for strategy in strategies:

        if -1 <= ((current_time / 1000) % strategy.interval[1]) <= 1:
            time.sleep(15)

            for asset in portfolio.assets:
                df_asset = create_dataframe(asset, strategy.interval[0], MA2)
                format_data_message(df_asset, asset, strategy.strategy_type)
                action = strategy.check_for_signal(df_asset, asset)

                if action == "BUY":
                    trade_amount = portfolio.calc_available_balance(strategy.ratio / len(portfolio.assets))
                    receipt = trader.post_order(0, asset=asset, quantity=round(trade_amount, 2), action=action)

                    if receipt == "SKIP":
                        break

                    elif receipt["status"] == "FILLED":
                        strategy.active_asset.append(asset)
                        portfolio.active_trades += (strategy.ratio / len(portfolio.assets))
                        key = f"{asset} {strategy.strategy_type.lower()}"
                        portfolio.coins[key] = float(receipt["executedQty"] * 0.997)
                        portfolio.balance = trader.get_balance(0, asset="EUR")
                        format_order_message(action, asset)

                elif action == "SELL":
                    key = f"{asset} {strategy.strategy_type.lower()}"
                    tick = trader.get_exchange_info(asset)
                    quantity = portfolio.calc_order_quantity(tick, key)
                    receipt = trader.post_order(0, asset=asset, quantity=quantity, action=action)

                    if receipt == "SKIP":
                        break

                    elif receipt["status"] == "FILLED":
                        strategy.active_asset.remove(asset)
                        portfolio.active_trades -= (strategy.ratio / len(portfolio.assets))
                        portfolio.coins[key] = 0
                        portfolio.balance = trader.get_balance(0, asset="EUR")
                        format_order_message(action, asset)

            just_posted = True

    if just_posted:
        time.sleep(60)
        just_posted = False
