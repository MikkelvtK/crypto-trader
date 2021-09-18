import hashlib
import hmac
from decorators import *


class TraderAPI:

    def __init__(self):
        self.key = config.apiKey
        self.secret = config.apiSecret
        self.header = {"X-MBX-APIKEY": self.key}
        self.endpoint = "https://api.binance.com"

    @check_response
    @connection_authenticator
    def get_latest_price(self, asset):
        symbol_price_ticker = "/api/v3/ticker/price"
        return requests.get(self.endpoint + symbol_price_ticker, params={"symbol": asset.upper()})

    @check_response
    @connection_authenticator
    def get_history(self, **kwargs):
        """Get history of asset price data"""
        candlestick_data = "/api/v3/klines"

        params = {
            "symbol": kwargs["symbol"].upper(),
            "interval": kwargs["interval"],
            "limit": kwargs["limit"],
        }

        return requests.get(self.endpoint + candlestick_data, params=params, headers=self.header)

    @check_response
    @connection_authenticator
    def get_balance(self):
        """Get balances of all assets of user"""

        # Prepare variables
        ms_time = round(time.time() * 1000)
        request = "/api/v3/account"

        # Create hashed signature
        query_string = f"timestamp={ms_time}"
        signature = hmac.new(self.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

        params = {
            "timestamp": ms_time,
            "signature": signature,
        }

        return requests.get(self.endpoint + request, params=params, headers=self.header)

    @check_response
    @connection_authenticator
    def post_order(self, **kwargs):
        # Prepare variables
        request = "/api/v3/order"
        asset = kwargs["asset"].upper()
        side = kwargs["action"].upper()
        order_type = kwargs["order_type"].upper()
        quantity_type = kwargs["quantity_type"]
        amount = kwargs["amount"]
        ms_time = round(time.time() * 1000)

        params = {
            "symbol": asset,
            "side": side,
            "type": order_type,
            quantity_type: amount,
            "timestamp": ms_time,
        }

        # Create hashed signature
        if order_type.lower() == "limit":
            price = kwargs["price"]
            params["price"] = price
            params["timeInForce"] = "GTC"

            query_string = f"symbol={asset}&side={side}&type={order_type}&" \
                           f"{quantity_type}={amount}&timestamp={ms_time}&price={price}&timeInForce=GTC"
        else:
            query_string = f"symbol={asset}&side={side}&type={order_type}&" \
                           f"{quantity_type}={amount}&timestamp={ms_time}"

        signature = hmac.new(self.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return requests.post(self.endpoint + request, params=params, headers=self.header)

    @check_response
    @connection_authenticator
    def get_exchange_info(self, asset):
        """Get asset information"""
        request = "/api/v3/exchangeInfo"
        return requests.get(self.endpoint + request, params={"symbol": asset})

    @check_response
    @connection_authenticator
    def query_order(self, asset_symbol, order_id, side, order_type):
        request = "/api/v3/order"
        ms_time = round(time.time() * 1000)
        symbol = asset_symbol.upper()

        params = {
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": ms_time,
        }

        query_string = f"symbol={symbol}&orderId={order_id}&timestamp={ms_time}"
        signature = hmac.new(self.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return requests.get(self.endpoint + request, params=params, headers=self.header)


if __name__ == "__main__":
    trader = TraderAPI()
    print(trader.get_exchange_info("VETEUR"))
