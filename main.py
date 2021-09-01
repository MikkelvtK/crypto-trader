from trader import TraderAPI
from strategies import *
from bot import TraderBot
from constants import *


def main():

    # Create all objects
    api_trader = TraderAPI()
    crossing_sma = CrossingSMA(MA1, MA2, interval=H4, assets=["veteur", "adaeur"], name="golden cross")
    bottom_rsi = BottomRSI(interval=H1, assets=["veteur", "adaeur", "hoteur"], name="rsi dips")
    bollinger = BollingerBands(interval=M30, assets=["veteur", "adaeur", "hoteur", "dogeeur", "trxeur"],
                               name="bol bands")
    strategies = (crossing_sma, bottom_rsi, bollinger)

    # Create bot object and activate it
    bot = TraderBot("john", api_trader, strategies)
    bot.activate()


if __name__ == "__main__":
    main()
