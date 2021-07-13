import pandas as pd
import requests
import datetime as dt
import time
import json
import hashlib
import hmac
from trader import Trader


def current_milli_time():
    return round(time.time() * 1000)

# query_string = f'timestamp={unix}'
# secret = ''

# signature = hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()


trader = Trader()
print(trader.get_latest_price("VETUSDT"))




