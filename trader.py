import requests
import hashlib
import hmac
import json


class Trader:
    def __init__(self):
        with open("config.json") as f:
            keys = json.load(f)

        self.key = keys["api_key"]
        self.secret = keys["api_secret"]
        self.endpoint = "https://api.binance.com"

    def get_latest_price(self, asset):
        symbol_price_ticker = "/api/v3/ticker/price"
        return requests.get(self.endpoint + symbol_price_ticker, params={"symbol": asset}).json()

    def get_history(self, symbol, interval, limit=1000):
        candlestick_data = "/api/v3/klines"
        header = {
            "apiKey": self.key,
            "apiSecret": self.secret
        }

        # Define parameters
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        return requests.get(self.endpoint + candlestick_data, params=params, headers=header).json()
