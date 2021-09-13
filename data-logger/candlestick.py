import datetime as dt
import math


class Candlestick:

    def __init__(self, interval, symbol, open_time, open_price):
        self.interval = interval
        self.symbol = symbol
        self.open_time = dt.datetime.utcfromtimestamp(math.floor(open_time))
        self.open_price = open_price
        self.high = open_price
        self.low = open_price
        self.close_price = open_price
        self.close_time = self.open_time + dt.timedelta(seconds=self.interval - 1)

    def update_attributes(self, price):
        self.close_price = price

        if price > self.high:
            self.high = price

        elif price < self.low:
            self.low = price
