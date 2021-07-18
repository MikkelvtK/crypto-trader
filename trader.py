import requests
import hashlib
import hmac
import time
import os


class TraderAPI:
    def __init__(self):
        self.key = os.environ.get("apiKey")
        self.secret = os.environ.get("apiSecret")
        self.header = {"X-MBX-APIKEY": self.key}
        self.endpoint = "https://api.binance.com"

    def get_latest_price(self, asset):
        symbol_price_ticker = "/api/v3/ticker/price"
        return requests.get(self.endpoint + symbol_price_ticker, params={"symbol": asset}).json()

    def get_history(self, symbol, interval, limit=1000):
        candlestick_data = "/api/v3/klines"

        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        return requests.get(self.endpoint + candlestick_data, params=params, headers=self.header).json()

    def get_balance(self):
        ms_time = round(time.time() * 1000)
        request = "/api/v3/account"
        query_string = f"timestamp={ms_time}"
        signature = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        params = {
            "timestamp": ms_time,
            "signature": signature,
        }

        response = requests.get(self.endpoint + request, params=params, headers=self.header).json()
        for balance in response["balances"]:
            if balance["asset"] == "EUR":
                return balance["free"]

    def post_order(self, asset, quantity, action):
        if action == "BUY":
            quantity_type = "quoteOrderQty"
        else:
            quantity_type = "quantity"
        side = action
        type_ = "MARKET"
        request = "/api/v3/order"
        ms_time = round(time.time() * 1000)
        query_string = f"symbol={asset}&side={side}&type={type_}&{quantity_type}={quantity}&timestamp={ms_time}"
        signature = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        params = {
            "symbol": asset,
            "side": side,
            "type": type_,
            quantity_type: quantity,
            "timestamp": ms_time,
            "signature": signature,
        }
        return requests.post(self.endpoint + request, params=params, headers=self.header).json()
