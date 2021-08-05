import pandas as pd
import pandas_ta as pta
import math

MA1 = 40
MA2 = 170
STD = 20


def create_dataframe(api, symbol, interval, limit):
    """Cleans data for the bot to use"""

    # Create and clean initial DataFrame
    df = pd.DataFrame(api.get_history(symbol=symbol, interval=interval, limit=limit))
    df = df.drop(columns=df.iloc[:, 2:].columns)
    df.columns = ["Open Time", "Price"]
    df = df.set_index("Open Time")
    df.index = pd.to_datetime(df.index, unit="ms")
    df = df.astype(float)

    # Calculate SMA
    df[f"SMA_{MA1}"] = df["Price"].rolling(window=MA1).mean()
    df[f"SMA_{MA2}"] = df["Price"].rolling(window=MA2).mean()

    # Calculate Bollinger bands
    df["Std"] = df["Price"].rolling(window=STD).std()
    df["Upper"] = df[f"SMA_{MA1}"] + 1.5 * df["Std"]
    df["Lower"] = df[f"SMA_{MA1}"] - 2.5 * df["Std"]

    # Calculate RSI with SMA
    df["RSI"] = pta.rsi(df["Price"], length=14)
    return df


def calc_true_order_quantity(trader, symbol, coins):
    """Get the step size for crypto currencies used by the api"""
    for asset in trader.get_exchange_info(symbol)["symbols"]:
        if asset["symbol"] == symbol:
            for binance_filter in asset["filters"]:
                if binance_filter['filterType'] == 'LOT_SIZE':
                    step_size = binance_filter['stepSize'].find('1') - 2
                    return math.floor(coins * 10 ** step_size) / float(10 ** step_size)


def calculate_rsi(df_column, window=14):
    """Calculates RSI for price"""
    delta = df_column.diff(1)

    positives = delta.copy()
    negatives = delta.copy()
    positives[positives < 0] = 0
    negatives[negatives > 0] = 0

    rs = positives.rolling(window).mean() / abs(negatives.rolling(window).mean())
    rsi = 100 - 100 / (1 + rs)
    return rsi
