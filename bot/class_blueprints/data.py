import pandas as pd
import pandas_ta as pta


class Data:

    def __init__(self, data):
        self._df = pd.DataFrame(data)
        self._clean_data()

    # ----- GETTERS / SETTERS ----- #

    @property
    def df(self):
        return self._df

    # ----- CLASS METHODS ----- #

    def _clean_data(self):
        self._df = self._df.drop(columns=self._df.columns[[1, 2, 3, 5, 6, 7, 8, 9, 10, 11]], axis=1)
        self._df.columns = ["Open Time", "Price"]
        self._df = self._df.set_index("Open Time")
        self._df.index = pd.to_datetime(self._df.index, unit="ms")
        self._df = self._df.astype(float)

    def set_sma(self, window):
        self._df[f"SMA_{window}"] = self._df["Price"].rolling(window=window).mean()

    def set_rsi(self):
        self._df["RSI"] = pta.rsi(self._df["Price"], length=14)

    def set_ema(self, window):
        self._df[f"EMA_{window}"] = pta.ema(self._df["Price"], length=window)
