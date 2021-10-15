import hashlib
import hmac
import config
from decorators import *


@check_response
@connection_authenticator
def get_latest_price(asset):
    endpoint = "https://api.binance.com/api/v3/ticker/price"
    return requests.get(endpoint, params={"symbol": asset.upper()})

@check_response
@connection_authenticator
def get_history(**kwargs):
    """Get history of asset price data"""
    endpoint = "https://api.binance.com/api/v3/klines"

    params = {
        "symbol": kwargs["symbol"].upper(),
        "interval": kwargs["interval"],
        "limit": kwargs["limit"],
    }

    return requests.get(endpoint, params=params, headers=config.header)

@check_response
@connection_authenticator
def get_balance():
    """Get balances of all assets of user"""

    # Prepare variables
    ms_time = round(time.time() * 1000)
    endpoint = "https://api.binance.com/api/v3/account"

    # Create hashed signature
    query_string = f"timestamp={ms_time}"
    signature = hmac.new(config.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    params = {
        "timestamp": ms_time,
        "signature": signature,
    }

    return requests.get(endpoint, params=params, headers=config.header)

@check_response
@connection_authenticator
def post_order(**kwargs):
    # Prepare variables
    endpoint = "https://api.binance.com/api/v3/order"
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

    signature = hmac.new(config.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
    params["signature"] = signature
    return requests.post(endpoint, params=params, headers=config.header)

@check_response
@connection_authenticator
def get_exchange_info(asset):
    """Get asset information"""
    endpoint = "https://api.binance.com/api/v3/exchangeInfo"
    return requests.get(endpoint, params={"symbol": asset.upper()})

@check_response
@connection_authenticator
def query_order(asset_symbol, order_id):
    endpoint = "https://api.binance.com/api/v3/order"
    ms_time = round(time.time() * 1000)
    symbol = asset_symbol.upper()

    params = {
        "symbol": symbol,
        "orderId": order_id,
        "timestamp": ms_time,
    }

    query_string = f"symbol={symbol}&orderId={order_id}&timestamp={ms_time}"
    signature = hmac.new(config.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
    params["signature"] = signature
    return requests.get(endpoint, params=params, headers=config.header)

@check_response
@connection_authenticator
def cancel_order(symbol, order_id):
    endpoint = "https://api.binance.com/api/v3/order"
    ms_time = round(time.time() * 1000)

    params = {
        "symbol": symbol.upper(),
        "orderId": order_id,
        "timestamp": ms_time,
    }

    query_string = f"symbol={symbol.upper()}&orderId={order_id}&timestamp={ms_time}"
    signature = hmac.new(config.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
    params["signature"] = signature
    return requests.delete(endpoint, params=params, headers=config.header)

@check_response
@connection_authenticator
def cancel_all_orders(symbol):
    endpoint = "https://api.binance.com/api/v3/openOrders"
    ms_time = round(time.time() * 1000)

    params = {
        "symbol": symbol.upper(),
        "timestamp": ms_time,
    }

    query_string = f"symbol={symbol.upper()}&timestamp={ms_time}"
    signature = hmac.new(config.secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
    params["signature"] = signature
    return requests.delete(endpoint, params=params, headers=config.header)
