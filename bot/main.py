import config
from class_blueprints.strategies import Strategy
from class_blueprints.crypto import Crypto
from trader_bot import TraderBot


def main():

    # Create all objects
    cryptos = [Crypto(key, config.FIAT_MARKET, value) for key, value in config.CRYPTOS.items()]

    strategies = []
    for crypto in cryptos:
        symbol = crypto.get_symbol()
        strategy = Strategy(symbol=symbol, name="Golden Cross")
        strategies.append(strategy)

    # Create bot object and activate it
    bot = TraderBot(name=config.BOT_NAME, strategies=strategies, cryptos=cryptos)
    bot.activate()


if __name__ == "__main__":
    main()
