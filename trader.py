import hashlib
import hmac
import time
from decorators import *


class TraderAPI:

    def __init__(self):
        self.key = os.environ.get("apiKey")
        self.secret = os.environ.get("apiSecret")
        self.header = {"X-MBX-APIKEY": self.key}
        self.endpoint = "https://api.binance.com"

    def get_latest_price(self, asset):
        symbol_price_ticker = "/api/v3/ticker/price"
        return requests.get(self.endpoint + symbol_price_ticker, params={"symbol": asset}).json()

    @check_response
    @connection_authenticator
    def get_history(self, **kwargs):
        candlestick_data = "/api/v3/klines"

        params = {
            "symbol": kwargs["symbol"],
            "interval": kwargs["interval"],
            "limit": kwargs["limit"],
        }

        return requests.get(self.endpoint + candlestick_data, params=params, headers=self.header)

    @check_response
    @connection_authenticator
    def get_balance(self):
        ms_time = round(time.time() * 1000)
        request = "/api/v3/account"
        query_string = f"timestamp={ms_time}"
        signature = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        params = {
            "timestamp": ms_time,
            "signature": signature,
        }

        return requests.get(self.endpoint + request, params=params, headers=self.header)

    @check_response
    @connection_authenticator
    def post_order(self, **kwargs):
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

        return requests.post(self.endpoint + request, params=params, headers=self.header)

    @check_response
    @connection_authenticator
    def get_exchange_info(self, asset):
        request = "/api/v3/exchangeInfo"
        return requests.get(self.endpoint + request, params={"symbol": asset})



