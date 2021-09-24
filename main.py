import config
from trader import TraderAPI
from strategies import *
from bot import TraderBot
from constants import *
from config import *


def main():

    # Create all objects
    api_trader = TraderAPI()
    crossing_sma = CrossingSMA(MA1, MA2, interval=H4, assets=HODL_ASSETS, name="golden cross")
    bottom_rsi = BottomRSI(interval=M1, assets=DAY_TRADING_ASSETS, name="rsi dips")
    bollinger = BollingerBands(interval=M30, assets=DAY_TRADING_ASSETS, name="bol bands")
    strategies = [crossing_sma, bottom_rsi]

    # Create bot object and activate it
    bot = TraderBot(config.BOT_NAME, api_trader, strategies, FIAT_MARKET)
    bot.activate()


if __name__ == "__main__":
    main()
