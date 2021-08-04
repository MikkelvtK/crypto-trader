import pandas as pd
import pandas_ta as pta

MA1 = 40
MA2 = 170
STD = 20


def create_dataframe(api, symbol, interval, limit):
    """Cleans data for the bot to use"""

    # Create and clean initial DataFrame
    df = pd.DataFrame(api.get_history(symbol=symbol, interval=interval, limit=limit))
    df = df.drop(columns=df.iloc[:, 2:].columns)
    df.columns = ["Open Time", "Price"]
    df = df.set_index("Open Time")
    df.index = pd.to_datetime(df.index, unit="ms")
    df = df.astype(float)

    # Calculate SMA
    df[f"SMA_{MA1}"] = df["Price"].rolling(window=MA1).mean()
    df[f"SMA_{MA2}"] = df["Price"].rolling(window=MA2).mean()

    # Calculate Bollinger bands
    df["Std"] = df["Price"].rolling(window=STD).std()
    df["Upper"] = df[f"SMA_{MA1}"] + 1.5 * df["Std"]
    df["Lower"] = df[f"SMA_{MA1}"] - 2.5 * df["Std"]

    # Calculate RSI with SMA
    df["RSI"] = pta.rsi(df["Price"], length=14)
    return df
