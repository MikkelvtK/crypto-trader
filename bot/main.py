import config
import constants
from bot.class_blueprints.strategies import CrossingSMA
from bot.class_blueprints.crypto import Crypto
from trader_bot import TraderBot


def main():

    # Create all objects
    cryptos = [Crypto(crypto, config.FIAT_MARKET) for crypto in config.CRYPTOS]

    strategies = []
    for crypto in cryptos:
        symbol = crypto.get_symbol()
        strategy = CrossingSMA(symbol=symbol, interval=constants.H4, name="Golden Cross")
        strategies.append(strategy)

    # Create bot object and activate it
    bot = TraderBot(name=config.BOT_NAME, strategies=strategies, cryptos=cryptos)
    bot.activate()


if __name__ == "__main__":
    main()
