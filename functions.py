import pandas as pd
import pandas_ta as pta
import math
from constants import *


def create_dataframe(data):
    """Cleans data for the bot to use"""

    # Create and clean initial DataFrame
    df = pd.DataFrame(data)
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
    df["MA_BOL"] = df["Price"].rolling(window=MA_BOL).mean()
    df["Upper"] = df["MA_BOL"] + 0.5 * df["Std"]
    df["Lower"] = df["MA_BOL"] - 2.0 * df["Std"]

    # Calculate RSI with SMA
    df["RSI"] = pta.rsi(df["Price"], length=14)
    return df


def calc_correct_quantity(step_size, coins):
    """Get the step size for crypto currencies used by the api"""
    if step_size < 0:
        return math.floor(coins)
    return math.floor(coins * 10 ** step_size) / 10 ** step_size


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
