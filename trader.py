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

        response = requests.get(self.endpoint + candlestick_data, params=params, headers=self.header)
        if response.ok:
            return response.json()
        else:
            print(response.text)
            time.sleep(5)
            self.get_history(symbol, interval, limit)

    def get_balance(self, asset):
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
            if balance["asset"] == asset:
                return float(balance["free"])

    def post_order(self, n, **kwargs):
        if n == 5:
            print("I failed to connect with the API. Breaking the cycle")
            return "BREAK"

        if kwargs["action"] == "BUY":
            quantity_type = "quoteOrderQty"
        else:
            quantity_type = "quantity"

        side = kwargs["action"]
        type_ = "MARKET"
        request = "/api/v3/order"
        ms_time = round(time.time() * 1000)

        query_string = f"symbol={kwargs['asset']}&side={side}&type={type_}&" \
                       f"{quantity_type}={kwargs['quantity']}&timestamp={ms_time}"
        signature = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        params = {
            "symbol": kwargs["asset"],
            "side": side,
            "type": type_,
            quantity_type: kwargs["quantity"],
            "timestamp": ms_time,
            "signature": signature,
        }

        response = requests.post(self.endpoint + request, params=params, headers=self.header)
        return self.check_response(self.post_order, n, response, kwargs)

    @classmethod
    def check_response(cls, func, n, response, kwargs):
        if response.ok:
            return response.json()
        else:
            print("There are some issues with the API connection. Please HODL.")
            time.sleep(5)
            return func(n+1, **kwargs)
