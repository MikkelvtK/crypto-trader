import time
import hashlib
import hmac
from trader import TraderAPI
from wallet import Portfolio
from strategies import *

MA1 = 50
MA2 = 200
SHORT_INTERVAL = "30m"
LONG_INTERVAL = "4h"


def calculate_rsi(df_column, window=14):
    delta = df_column.diff(1)

    positives = delta.copy()
    negatives = delta.copy()
    positives[positives < 0] = 0
    negatives[negatives > 0] = 0

    rs = positives.rolling(window).mean() / abs(negatives.rolling(window).mean())
    rsi = 100 - 100 / (1 + rs)
    return rsi


def current_ms_time():
    return round(time.time() * 1000)


def create_dataframe(symbol, interval, limit):
    df = pd.DataFrame(trader.get_history(symbol, interval, limit=limit))
    df = df.drop(columns=df.iloc[:, 1:4].columns)
    df = df.drop(columns=df.iloc[:, 2:].columns)
    df.columns = ["Open Time", "Price"]
    df = df.set_index("Open Time")
    df.index = pd.to_datetime(df.index, unit="ms")
    df = df.astype(float)
    df[f"SMA_{MA1}"] = df["Price"].rolling(window=MA1).mean()
    df[f"SMA_{MA2}"] = df["Price"].rolling(window=MA2).mean()
    df["RSI"] = calculate_rsi(df["Price"])
    return df


trader = TraderAPI()
wallet = Portfolio(250)
crossing_sma = CrossingSMA(MA1, MA2)
bottom_rsi = BottomRSI(MA1, MA2)

counter = 0
while True:
    for asset in wallet.assets:
        df_asset_30m = create_dataframe(asset, SHORT_INTERVAL, MA2)
        print(f"<--------------------RETRIEVING DATA FOR {asset} SHORT TERM STRATEGY------------------------>:\n"
              f"{df_asset_30m.iloc[[-1]]}")
        bottom_rsi.check_for_signal(df_asset_30m)
        if counter % 8 == 0:
            df_asset_4h = create_dataframe(asset, LONG_INTERVAL, MA2)
            counter = 0
            print(f"<--------------------RETRIEVING DATA FOR {asset} LONG TERM STRATEGY------------------------->:\n"
                  f"{df_asset_4h.iloc[[-1]]}")
            crossing_sma.check_for_signal(df_asset_4h)

    time.sleep(1800)
    counter += 1






# query_string = f'timestamp={unix}'
# secret = ''

# signature = hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()


