import config
from sqlalchemy import create_engine
from class_blueprints.strategies import Strategy
from class_blueprints.crypto import Crypto
from trader_bot import TraderBot
from class_blueprints.trader import TraderAPI


def main():
    engine = create_engine(f"sqlite:///{config.db_path}")

    # Create all objects
    cryptos = [Crypto(key, config.FIAT_MARKET, value) for key, value in config.CRYPTOS.items()]
    api = TraderAPI()

    strategies = []
    for crypto in cryptos:
        symbol = crypto.get_symbol()
        strategy = Strategy(symbol=symbol, name="Golden Cross", api=api)
        strategies.append(strategy)

    # Create bot object and activate it
    bot = TraderBot(name=config.BOT_NAME, strategies=strategies, cryptos=cryptos, api=api)
    bot.activate()


if __name__ == "__main__":
    main()
