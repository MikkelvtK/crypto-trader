import requests
import hashlib
import hmac
import json
import time


class TraderAPI:
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

    def get_balance(self):
        ms_time = round(time.time() * 1000)
        request = "/api/v3/account"
        query_string = f"timestamp={ms_time}"
        signature = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        header = {"X-MBX-APIKEY": self.key}
        params = {
            "timestamp": ms_time,
            "signature": signature,
        }

        response = requests.get(self.endpoint + request, params=params, headers=header).json()
        for balance in response["balances"]:
            if balance["asset"] == "USD":
                return balance["free"]
        return 0
