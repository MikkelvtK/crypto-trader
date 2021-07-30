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

    def get_history(self, n, **kwargs):
        if n == 5:
            print("I failed to connect with the API. Breaking the cycle")
            return

        candlestick_data = "/api/v3/klines"

        params = {
            "symbol": kwargs["symbol"],
            "interval": kwargs["interval"],
            "limit": kwargs["limit"],
        }

        response = requests.get(self.endpoint + candlestick_data, params=params, headers=self.header)
        return self.check_response(self.get_history, n, response, kwargs)

    def get_balance(self, n, **kwargs):
        if n == 5:
            print("I failed to connect with the API. Breaking the cycle")
            return 0

        ms_time = round(time.time() * 1000)
        request = "/api/v3/account"
        query_string = f"timestamp={ms_time}"
        signature = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        params = {
            "timestamp": ms_time,
            "signature": signature,
        }

        response = requests.get(self.endpoint + request, params=params, headers=self.header)
        response_json = self.check_response(self.get_balance, n, response, kwargs)
        for balance in response_json["balances"]:
            if balance["asset"] == kwargs["asset"]:
                return float(balance["free"])

    def post_order(self, n, **kwargs):
        if n == 5:
            print("I failed to connect with the API. Breaking the cycle")
            return "SKIP"

        if kwargs["action"] == "BUY":
            quantity_type = "quoteOrderQty"
        else:
            quantity_type = "quantity"

        side = kwargs["action"]
        type_ = "MARKET"
        request = "/api/v3/order/test"
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

    def get_exchange_info(self, asset):
        request = "/api/v3/exchangeInfo"
        response = requests.get(self.endpoint + request, params={"symbol": asset}).json()

        for symbol in response["symbols"]:
            if symbol["symbol"] == asset:
                for binance_filter in symbol["filters"]:
                    if binance_filter['filterType'] == 'LOT_SIZE':
                        return binance_filter['stepSize'].find('1') - 2

    @staticmethod
    def check_response(func, n, response, kwargs):
        if response.ok:
            return response.json()
        else:
            print("There are some issues with the API connection. Please HODL.")
            time.sleep(5)
            return func(n+1, **kwargs)
