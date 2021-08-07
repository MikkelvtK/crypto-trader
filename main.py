from trader import TraderAPI
from strategies import *
from bot import TraderBot

MA1 = 40
MA2 = 170
STD = 20
M30 = ("30m", 1800)
M15 = ("15m", 900)
M1 = ("1m", 60)
H4 = ("4h", 14400)
H1 = ("1h", 3600)


def main():

    # Create all objects
    api_trader = TraderAPI()
    crossing_sma = CrossingSMA(MA1, MA2, interval=H4, assets=["veteur", "linkeur"], name="golden cross")
    bottom_rsi = BottomRSI(interval=H1, assets=["veteur"], name="rsi dips")
    bollinger = BollingerBands(interval=M15, assets=["veteur", "linkeur", "adaeur"], name="bol bands")
    strategies = (crossing_sma, bottom_rsi, bollinger)

    # Create bot object and activate it
    bot = TraderBot("john", api_trader, strategies)
    bot.activate()


if __name__ == "__main__":
    main()
