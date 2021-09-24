import pandas as pd
import pandas_ta as pta
import math
from constants import *


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
